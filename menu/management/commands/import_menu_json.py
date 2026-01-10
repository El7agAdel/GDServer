import json
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction

from menu.models import MenuCategory, MenuItem


def _pick_price_egp(drink: dict) -> int:
    """
    menu.json sometimes has `price`, sometimes only `sizes`.
    We pick:
      - drink["price"] if present
      - else the smallest size price if `sizes` exists
    Returns price in EGP as int.
    """
    if drink.get("price") is not None:
        return int(drink["price"])

    sizes = drink.get("sizes") or []
    if sizes:
        # pick minimum price across sizes
        return int(min(s.get("price", 0) for s in sizes if s.get("price") is not None))

    raise ValueError(f"No price found for drink: {drink.get('name')} ({drink.get('id')})")


def _set_if_field_exists(obj, field_name: str, value):
    """Set model field if it exists (keeps command compatible with different schemas)."""
    if hasattr(obj, field_name):
        setattr(obj, field_name, value)


class Command(BaseCommand):
    help = "Import menu categories/items from menu.json (categories + drinks)."

    def add_arguments(self, parser):
        parser.add_argument(
            "--path",
            type=str,
            default="menu.json",
            help="Path to JSON file (default: menu.json in project root)",
        )
        parser.add_argument(
            "--wipe",
            action="store_true",
            help="Delete existing MenuCategory/MenuItem before importing.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        path = Path(options["path"])
        wipe = options["wipe"]

        if not path.exists():
            raise CommandError(f"JSON file not found: {path}")

        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as e:
            raise CommandError(f"Invalid JSON: {e}")

        categories = data.get("categories") or []
        drinks = data.get("drinks") or []

        if not categories:
            raise CommandError("menu.json: 'categories' is missing/empty")
        if not drinks:
            raise CommandError("menu.json: 'drinks' is missing/empty")

        if wipe:
            self.stdout.write(self.style.WARNING("Wiping existing menu data..."))
            MenuItem.objects.all().delete()
            MenuCategory.objects.all().delete()

        # 1) Create / update categories
        category_map = {}  # category_name -> MenuCategory instance
        created_categories = 0
        updated_categories = 0

        for idx, cat in enumerate(categories, start=1):
            name = (cat.get("name") or "").strip()
            if not name:
                continue

            obj, created = MenuCategory.objects.get_or_create(
                name=name,
                defaults={"sort_order": idx},
            )

            # Optional fields if your model has them
            _set_if_field_exists(obj, "description", (cat.get("description") or "").strip())
            _set_if_field_exists(obj, "sort_order", idx)
            _set_if_field_exists(obj, "external_id", (cat.get("id") or "").strip())

            obj.save()

            category_map[name] = obj
            if created:
                created_categories += 1
            else:
                updated_categories += 1

        # 2) Create / update items
        created_items = 0
        updated_items = 0
        skipped_items = 0

        # keep per-category ordering consistent
        per_cat_sort = {name: 0 for name in category_map.keys()}

        for d in drinks:
            item_name = (d.get("name") or "").strip()
            cat_name = (d.get("category") or "").strip()

            if not item_name or not cat_name:
                skipped_items += 1
                continue

            category_obj = category_map.get(cat_name)
            if not category_obj:
                # category in drinks not present in categories array
                skipped_items += 1
                continue

            try:
                price_egp = _pick_price_egp(d)
            except Exception:
                skipped_items += 1
                continue

            per_cat_sort[cat_name] = per_cat_sort.get(cat_name, 0) + 1
            sort_order = per_cat_sort[cat_name]

            defaults = {
                "price_egp": int(price_egp),
                "is_available": True,
                "sort_order": sort_order,
            }

            # If your MenuItem model has description
            defaults["description"] = (d.get("description") or "").strip()
            if hasattr(MenuItem, "sizes"):
                defaults["sizes"] = d.get("sizes") or []

            obj, created = MenuItem.objects.update_or_create(
                category=category_obj,
                name=item_name,
                defaults=defaults,
            )

            # Optional: save external id if field exists
            _set_if_field_exists(obj, "external_id", (d.get("id") or "").strip())
            obj.save()

            if created:
                created_items += 1
            else:
                updated_items += 1

        self.stdout.write(self.style.SUCCESS("Import complete ✅"))
        self.stdout.write(f"Categories created: {created_categories}, updated: {updated_categories}")
        self.stdout.write(f"Items created: {created_items}, updated: {updated_items}, skipped: {skipped_items}")
