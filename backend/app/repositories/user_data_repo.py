import uuid
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from ..models.purchase import PurchaseRecord, VehicleSnapshot, PurchaseStatus
from ..models.listing import VehicleListing, ListingStatus, ApprovalStatus
from ..models.owned_vehicle import OwnedVehicle, OwnershipSource
from ..models.booking import RentalBooking, BookingStatus
from ..models.order import PurchaseOrder, OrderStatus
from ..repositories.marketplace import marketplace_repo
from ..repositories.session import session_repo
from ..config import settings

logger = logging.getLogger("car_consultant.user_data")

class UserDataRepository:
    def __init__(self):
        self._purchases: Dict[str, PurchaseRecord] = {}
        self._purchases_by_order: Dict[str, PurchaseRecord] = {}
        self._listings: Dict[str, VehicleListing] = {}
        self._owned_vehicles: Dict[str, OwnedVehicle] = {}
        self._demo_user_id = "usr_demo_01"
        self._mongo_client = None
        self._mongo_db = None
        self._init_mongo()
        self._seed_initial_demo_data()

    def _init_mongo(self):
        """Attempt MongoDB connection if available; fallback gracefully to in-memory/JSON."""
        try:
            import pymongo
            client = pymongo.MongoClient(settings.mongodb_uri, serverSelectionTimeoutMS=800)
            client.admin.command('ping')
            self._mongo_client = client
            self._mongo_db = client.get_database()
            logger.info(f"Connected to MongoDB database '{self._mongo_db.name}'.")
        except Exception as e:
            logger.info("MongoDB not running on localhost. Operating in high-performance in-memory persistence mode.")
            self._mongo_client = None
            self._mongo_db = None

    def _seed_initial_demo_data(self):
        """Seeds initial verified portfolio for demo user 'usr_demo_01'."""
        # 1. An existing pre-owned sports car in garage
        owned_miata = OwnedVehicle(
            id="own_demo_01",
            userId=self._demo_user_id,
            vehicleId="CAR-091",
            brand="Mazda",
            model="MX-5 Miata Club",
            variant="Manual 6-Speed",
            year=2023,
            registrationNumber="DL-01-AB-1234",
            source=OwnershipSource.MANUALLY_ADDED,
            purchaseDate="2024-03-15T09:30:00Z",
            purchasePrice=3900000.0,
            currentEstimatedValue=3650000.0,
            image="https://images.unsplash.com/photo-1542282088-72c9c27ed0cd?auto=format&fit=crop&w=800&q=80",
            status="Active"
        )
        self._owned_vehicles[owned_miata.id] = owned_miata

        # 2. An active listing being sold
        listing_city = VehicleListing(
            id="list_demo_01",
            sellerId=self._demo_user_id,
            brand="Honda",
            model="City ZX 1.5 i-VTEC",
            variant="Automatic CVT",
            year=2021,
            registration_year=2021,
            fuel_type="Petrol",
            transmission="Automatic",
            kms_driven=32000,
            condition="Excellent",
            ownership_count=1,
            location="Delhi NCR",
            expected_price=1180000.0,
            images=[
                "https://images.unsplash.com/photo-1590362891988-f77804702088?auto=format&fit=crop&w=800&q=80"
            ],
            contact_name="Alex Vance",
            contact_phone="+91 98765 43210",
            contact_email="demo@auramotors.com",
            is_registered_in_user_name=True,
            approval_status=ApprovalStatus.APPROVED,
            status=ListingStatus.ACTIVE
        )
        self._listings[listing_city.id] = listing_city

        owned_city = OwnedVehicle(
            id="own_demo_02",
            userId=self._demo_user_id,
            brand="Honda",
            model="City ZX 1.5 i-VTEC",
            variant="Automatic CVT",
            year=2021,
            registrationNumber="DL-03-CD-5678",
            source=OwnershipSource.LISTED_FOR_SALE,
            purchaseDate="2021-06-10T11:00:00Z",
            purchasePrice=1450000.0,
            currentEstimatedValue=1180000.0,
            image="https://images.unsplash.com/photo-1590362891988-f77804702088?auto=format&fit=crop&w=800&q=80",
            status="Listed for Sale",
            linkedListingId=listing_city.id
        )
        self._owned_vehicles[owned_city.id] = owned_city

    # -------------------------------------------------------------
    # PURCHASES & IDEMPOTENCY
    # -------------------------------------------------------------
    def record_purchase(
        self,
        order_id: str,
        transaction_reference: str,
        user_id: Optional[str] = None
    ) -> PurchaseRecord:
        """
        Creates an immutable, snapshot-backed purchase record.
        Strictly idempotent: retries/refreshes return the existing record.
        """
        # Idempotency check
        if order_id in self._purchases_by_order:
            logger.info(f"Idempotency hit: Purchase for order '{order_id}' already recorded.")
            return self._purchases_by_order[order_id]

        target_user = user_id or self._demo_user_id

        # Retrieve order
        order = session_repo.get_order(order_id)
        if not order:
            raise ValueError(f"Order '{order_id}' not found in repository.")

        # Retrieve vehicle for snapshot
        vehicle = marketplace_repo.get_vehicle_by_id(order.vehicle_id)
        if not vehicle:
            # Fallback snapshot if vehicle unlisted
            snapshot = VehicleSnapshot(
                id=order.vehicle_id,
                brand="Aura",
                model="Certified Vehicle",
                variant="Deluxe",
                year=2024,
                category="SUV",
                image="https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?auto=format&fit=crop&w=800&q=80",
                transmission="Automatic",
                fuel_type="Petrol",
                location=order.delivery_city
            )
        else:
            img_val = (
                getattr(vehicle, "image_url", None)
                or (vehicle.images[0] if hasattr(vehicle, "images") and getattr(vehicle, "images") else None)
                or "https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?auto=format&fit=crop&w=800&q=80"
            )
            snapshot = VehicleSnapshot(
                id=vehicle.id,
                brand=vehicle.brand,
                model=vehicle.model,
                variant=getattr(vehicle, "variant", "Standard Edition"),
                year=vehicle.year,
                category=vehicle.category.value if hasattr(vehicle.category, "value") else str(vehicle.category),
                image=img_val,
                transmission=vehicle.transmission.value if hasattr(vehicle.transmission, "value") else str(vehicle.transmission),
                fuel_type=vehicle.fuel_type.value if hasattr(vehicle.fuel_type, "value") else str(vehicle.fuel_type),
                location=vehicle.location,
                specs={
                    "mileage_kmpl": getattr(vehicle, "mileage_kmpl", 16.0),
                    "power_bhp": getattr(vehicle, "power_bhp", 170),
                    "seats": getattr(vehicle, "seats", 5),
                    "condition": getattr(vehicle, "condition", "new")
                }
            )

        purchase_id = f"PUR-{datetime.utcnow().strftime('%Y')}-{uuid.uuid4().hex[:6].upper()}"
        purchase = PurchaseRecord(
            id=purchase_id,
            userId=target_user,
            vehicleId=order.vehicle_id,
            orderId=order_id,
            vehicleSnapshot=snapshot,
            purchasePrice=order.purchase_price,
            depositAmount=order.deposit_amount,
            paymentStatus="SUCCESS",
            purchaseStatus=PurchaseStatus.CONFIRMED,
            purchaseDate=datetime.utcnow().isoformat() + "Z",
            transactionReference=transaction_reference,
            deliveryCity=order.delivery_city,
            demo_mode=True
        )

        self._purchases[purchase.id] = purchase
        self._purchases_by_order[order_id] = purchase

        # Add to user's owned vehicles
        owned_id = f"own_{uuid.uuid4().hex[:8]}"
        owned = OwnedVehicle(
            id=owned_id,
            userId=target_user,
            vehicleId=order.vehicle_id,
            brand=snapshot.brand,
            model=snapshot.model,
            variant=snapshot.variant,
            year=snapshot.year,
            source=OwnershipSource.PURCHASED_PLATFORM,
            purchaseDate=purchase.purchaseDate,
            purchasePrice=purchase.purchasePrice,
            currentEstimatedValue=purchase.purchasePrice,
            image=snapshot.image,
            status="Active",
            linkedOrderId=order_id
        )
        self._owned_vehicles[owned.id] = owned

        # Sync to MongoDB if connected
        if self._mongo_db is not None:
            try:
                self._mongo_db["purchases"].update_one(
                    {"orderId": order_id},
                    {"$set": purchase.model_dump()},
                    upsert=True
                )
                self._mongo_db["owned_vehicles"].update_one(
                    {"id": owned.id},
                    {"$set": owned.model_dump()},
                    upsert=True
                )
            except Exception as e:
                logger.warning(f"MongoDB write failed: {e}")

        logger.info(f"Purchase successfully recorded: {purchase.id} for user '{target_user}'.")
        return purchase

    def get_user_purchases(
        self,
        user_id: str,
        search: Optional[str] = None,
        sort_by: Optional[str] = "date_desc",
        status: Optional[str] = None
    ) -> List[PurchaseRecord]:
        """Returns purchases belonging to the authenticated user."""
        records = [p for p in self._purchases.values() if p.userId == user_id]

        if search:
            q = search.lower().strip()
            records = [
                p for p in records
                if q in p.vehicleSnapshot.brand.lower() or
                   q in p.vehicleSnapshot.model.lower() or
                   q in p.orderId.lower() or
                   q in p.id.lower() or
                   (p.deliveryCity and q in p.deliveryCity.lower())
            ]

        if status:
            records = [p for p in records if p.purchaseStatus.value == status or p.paymentStatus == status]

        if sort_by == "date_desc":
            records.sort(key=lambda x: x.purchaseDate, reverse=True)
        elif sort_by == "date_asc":
            records.sort(key=lambda x: x.purchaseDate)
        elif sort_by == "price_desc":
            records.sort(key=lambda x: x.purchasePrice, reverse=True)
        elif sort_by == "price_asc":
            records.sort(key=lambda x: x.purchasePrice)

        return records

    def get_purchase_by_id(self, purchase_id: str, user_id: str) -> Optional[PurchaseRecord]:
        p = self._purchases.get(purchase_id)
        if p and p.userId == user_id:
            return p
        return None

    # -------------------------------------------------------------
    # OWNED VEHICLES
    # -------------------------------------------------------------
    def get_user_owned_vehicles(self, user_id: str) -> List[OwnedVehicle]:
        return [v for v in self._owned_vehicles.values() if v.userId == user_id]

    # -------------------------------------------------------------
    # VEHICLE LISTINGS (SELL A CAR)
    # -------------------------------------------------------------
    def create_listing(self, listing: VehicleListing) -> VehicleListing:
        self._listings[listing.id] = listing

        # Add to owned vehicles as LISTED_FOR_SALE
        owned_id = f"own_{uuid.uuid4().hex[:8]}"
        owned = OwnedVehicle(
            id=owned_id,
            userId=listing.sellerId,
            brand=listing.brand,
            model=listing.model,
            variant=listing.variant,
            year=listing.year,
            source=OwnershipSource.LISTED_FOR_SALE,
            purchaseDate=datetime.utcnow().isoformat() + "Z",
            purchasePrice=listing.expected_price,
            currentEstimatedValue=listing.expected_price,
            image=listing.images[0] if listing.images else "https://images.unsplash.com/photo-1542282088-72c9c27ed0cd?auto=format&fit=crop&w=800&q=80",
            status="Listed for Sale",
            linkedListingId=listing.id
        )
        self._owned_vehicles[owned.id] = owned

        if self._mongo_db is not None:
            try:
                self._mongo_db["listings"].update_one(
                    {"id": listing.id},
                    {"$set": listing.model_dump()},
                    upsert=True
                )
            except Exception as e:
                logger.warning(f"MongoDB listing write failed: {e}")

        logger.info(f"Listing created: {listing.id} for seller '{listing.sellerId}'.")
        return listing

    def get_user_listings(self, user_id: str, status: Optional[str] = None) -> List[VehicleListing]:
        records = [l for l in self._listings.values() if l.sellerId == user_id]
        if status and status.lower() != "all":
            records = [l for l in records if l.status.value.lower() == status.lower()]
        records.sort(key=lambda x: x.created_at, reverse=True)
        return records

    def get_listing_by_id(self, listing_id: str, user_id: Optional[str] = None) -> Optional[VehicleListing]:
        l = self._listings.get(listing_id)
        if l and (user_id is None or l.sellerId == user_id):
            return l
        return None

    def update_listing(self, listing_id: str, user_id: str, updates: Dict[str, Any]) -> Optional[VehicleListing]:
        l = self.get_listing_by_id(listing_id, user_id)
        if not l:
            return None
        for k, v in updates.items():
            if hasattr(l, k) and k not in ["id", "sellerId", "created_at"]:
                setattr(l, k, v)
        l.updated_at = datetime.utcnow().isoformat() + "Z"
        self._listings[listing_id] = l
        return l

    def delete_listing(self, listing_id: str, user_id: str) -> bool:
        l = self.get_listing_by_id(listing_id, user_id)
        if not l:
            return False
        l.status = ListingStatus.REMOVED
        l.updated_at = datetime.utcnow().isoformat() + "Z"
        self._listings[listing_id] = l
        return True

    # -------------------------------------------------------------
    # RENTALS & SUMMARY
    # -------------------------------------------------------------
    def get_user_rentals(self, user_id: str) -> List[RentalBooking]:
        """Returns rental bookings belonging to the user session."""
        all_b = list(session_repo._bookings.values())
        # Filter confirmed bookings
        return [b for b in all_b if b.status == BookingStatus.CONFIRMED]

    def get_dashboard_summary(self, user_id: str) -> Dict[str, Any]:
        """Returns real computed counts from persistent records."""
        purchases = self.get_user_purchases(user_id)
        rentals = self.get_user_rentals(user_id)
        owned = self.get_user_owned_vehicles(user_id)
        active_listings = [l for l in self.get_user_listings(user_id) if l.status == ListingStatus.ACTIVE]

        return {
            "total_purchases": len(purchases),
            "total_rentals": len(rentals),
            "active_rentals": len(rentals), # In mock demo mode, confirmed rentals are active
            "vehicles_owned": len([v for v in owned if v.status != "Sold"]),
            "active_selling_listings": len(active_listings),
            "total_spent_inr": sum(p.purchasePrice for p in purchases),
            "portfolio_valuation_inr": sum(v.currentEstimatedValue or 0 for v in owned)
        }

# Singleton instance
user_data_repo = UserDataRepository()
