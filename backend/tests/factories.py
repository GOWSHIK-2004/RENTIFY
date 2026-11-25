from decimal import Decimal

from app.models import Category, InventoryUnit, Product, User, UserRole
from app.utils.security import create_access_token, hash_password

PASSWORD = "correct-horse-battery"


def make_user(db, email: str, role: UserRole = UserRole.CUSTOMER, name: str = "Test User") -> User:
    user = User(full_name=name, email=email, password_hash=hash_password(PASSWORD), role=role)
    db.add(user)
    db.commit()
    return user


def auth_headers(user: User) -> dict[str, str]:
    return {"Authorization": f"Bearer {create_access_token(user.id, user.role.value)}"}


def make_category(db, name: str = "Cameras", slug: str | None = None, is_active: bool = True) -> Category:
    category = Category(name=name, slug=slug or name.lower().replace(" ", "-"), is_active=is_active)
    db.add(category)
    db.commit()
    return category


def make_product(db, category: Category, name: str = "Sony Alpha A6400", brand: str = "Sony",
                 daily_price: str = "899.00", **extra) -> Product:
    product = Product(
        category_id=category.id,
        name=name,
        brand=brand,
        model=extra.pop("model", name),
        short_description="Short description",
        description="Long description",
        daily_price=Decimal(daily_price),
        specifications={"Sensor": "APS-C"},
        **extra,
    )
    db.add(product)
    db.commit()
    return product


def make_unit(db, product: Product, asset_code: str, **extra) -> InventoryUnit:
    unit = InventoryUnit(product_id=product.id, asset_code=asset_code, **extra)
    db.add(unit)
    db.commit()
    return unit
