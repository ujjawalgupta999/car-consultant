import uuid
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from ..models.payment import PaymentRecord, PaymentStatus, TransactionType
from ..models.purchase import PurchaseRecord, VehicleSnapshot, PurchaseStatus
from ..models.rental import RentalRecord, RentalStatus
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
        self._payments: Dict[str, PaymentRecord] = {}
        self._payments_by_order: Dict[str, PaymentRecord] = {}
        self._payments_by_idemp: Dict[str, PaymentRecord] = {}
        self._purchases: Dict[str, PurchaseRecord] = {}
        self._purchases_by_order: Dict[str, PurchaseRecord] = {}
        self._rentals: Dict[str, RentalRecord] = {}
        self._rentals_by_order: Dict[str, RentalRecord] = {}
        self._listings: Dict[str, VehicleListing] = {}
        self._owned_vehicles: Dict[str, OwnedVehicle] = {}
        self._demo_user_id = "usr_demo_01"
        self._mongo_client = None
        self._mongo_db = None
        self._init_mongo()
        self._seed_initial_demo_data()

    def _init_mongo(self):
        """Attempt MongoDB connection if available; fallback gracefully to in-memory/JSON."""
        import os
        if getattr(settings, "storage_backend", "auto") in ["inmemory", "json"] or os.environ.get("STORAGE_BACKEND") == "inmemory":
            self._mongo_client = None
            self._mongo_db = None
            return

        try:
            from ..db.mongodb import mongodb_manager
            if mongodb_manager.is_connected() or mongodb_manager.connect():
                self._mongo_client = mongodb_manager._client
                self._mongo_db = mongodb_manager.get_database()
                logger.info(f"UserDataRepository linked to MongoDB database '{self._mongo_db.name}'.")
            else:
                self._mongo_client = None
                self._mongo_db = None
                logger.info("MongoDB not connected. Operating in high-performance in-memory persistence mode.")
        except Exception as e:
            logger.info(f"MongoDB initialization notice: {e}. Operating in in-memory persistence mode.")
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

        # 3. Seed initial historical rental booking for demo user
        rental_snap = VehicleSnapshot(
            id="CAR-001",
            brand="Hyundai",
            model="Creta SX (O)",
            variant="1.5 Petrol IVT",
            year=2024,
            category="SUV",
            image="https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?auto=format&fit=crop&w=800&q=80",
            transmission="Automatic",
            fuel_type="Petrol",
            location="Delhi NCR",
            specs={"seats": 5, "mileage_kmpl": 17.0}
        )
        seed_rental_id = "RNT-2026-INIT01"
        seed_booking_id = "BK-2026-90412"
        seed_rental_pay_id = "PAY-20260401-INIT01"
        seed_rental_txn = "TXN-MOCK-INIT90412"

        seed_payment = PaymentRecord(
            id=seed_rental_pay_id,
            userId=self._demo_user_id,
            orderId=seed_booking_id,
            transactionId=seed_rental_txn,
            vehicleId="CAR-001",
            transactionType=TransactionType.RENT,
            amount=18290.0,
            currency="INR",
            paymentMethod="upi",
            paymentStatus=PaymentStatus.SUCCESS,
            paymentProvider="MOCK_PAYMENT",
            paymentReference=seed_rental_txn,
            createdAt="2026-04-01T10:00:00Z",
            updatedAt="2026-04-01T10:00:00Z"
        )
        self._payments[seed_payment.id] = seed_payment
        self._payments_by_order[seed_booking_id] = seed_payment

        seed_rental = RentalRecord(
            id=seed_rental_id,
            userId=self._demo_user_id,
            vehicleId="CAR-001",
            paymentId=seed_rental_pay_id,
            orderId=seed_booking_id,
            vehicleSnapshot=rental_snap,
            pickupDate="2026-04-10",
            returnDate="2026-04-15",
            durationDays=5,
            pickupLocation="Delhi NCR",
            returnLocation="Delhi NCR",
            dailyRentalPrice=3200.0,
            rentalAmount=18290.0,
            securityDeposit=5000.0,
            rentalStatus=RentalStatus.CONFIRMED,
            paymentStatus="SUCCESS",
            transactionReference=seed_rental_txn,
            createdAt="2026-04-01T10:00:00Z",
            updatedAt="2026-04-01T10:00:00Z"
        )
        self._rentals[seed_rental.id] = seed_rental
        self._rentals_by_order[seed_booking_id] = seed_rental

        # 4. Seed initial historical purchase order for demo user
        purchase_snap = VehicleSnapshot(
            id="CAR-022",
            brand="Tata",
            model="Harrier Fearless Plus",
            variant="2.0 Kryotec Automatic",
            year=2024,
            category="SUV",
            image="https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?auto=format&fit=crop&w=800&q=80",
            transmission="Automatic",
            fuel_type="Diesel",
            location="Delhi NCR",
            specs={"seats": 5, "mileage_kmpl": 16.5}
        )
        seed_purch_id = "PUR-2026-INIT01"
        seed_order_id = "ORD-2026-88124"
        seed_purch_pay_id = "PAY-20260320-INIT02"
        seed_purch_txn = "TXN-MOCK-INIT88124"

        seed_purch_payment = PaymentRecord(
            id=seed_purch_pay_id,
            userId=self._demo_user_id,
            orderId=seed_order_id,
            transactionId=seed_purch_txn,
            vehicleId="CAR-022",
            transactionType=TransactionType.BUY,
            amount=2640000.0,
            currency="INR",
            paymentMethod="card",
            paymentStatus=PaymentStatus.SUCCESS,
            paymentProvider="MOCK_PAYMENT",
            paymentReference=seed_purch_txn,
            createdAt="2026-03-20T14:30:00Z",
            updatedAt="2026-03-20T14:30:00Z"
        )
        self._payments[seed_purch_payment.id] = seed_purch_payment
        self._payments_by_order[seed_order_id] = seed_purch_payment

        seed_purchase = PurchaseRecord(
            id=seed_purch_id,
            userId=self._demo_user_id,
            vehicleId="CAR-022",
            paymentId=seed_purch_pay_id,
            orderId=seed_order_id,
            vehicleSnapshot=purchase_snap,
            purchasePrice=2640000.0,
            purchaseStatus=PurchaseStatus.CONFIRMED,
            paymentStatus="SUCCESS",
            transactionReference=seed_purch_txn,
            purchaseDate="2026-03-20T14:30:00Z",
            createdAt="2026-03-20T14:30:00Z",
            updatedAt="2026-03-20T14:30:00Z"
        )
        self._purchases[seed_purchase.id] = seed_purchase
        self._purchases_by_order[seed_order_id] = seed_purchase

    # -------------------------------------------------------------
    # UNIFIED PAYMENTS & IDEMPOTENCY
    # -------------------------------------------------------------
    def record_payment(
        self,
        payment: PaymentRecord,
        idempotency_key: Optional[str] = None
    ) -> PaymentRecord:
        """
        Stores payment record and indexes by ID, orderId, and idempotency key.
        Prevents duplicate charges.
        """
        if idempotency_key:
            if idempotency_key in self._payments_by_idemp:
                logger.info(f"Idempotency hit: Payment for key '{idempotency_key}' already recorded.")
                return self._payments_by_idemp[idempotency_key]
            self._payments_by_idemp[idempotency_key] = payment

        self._payments[payment.id] = payment
        self._payments_by_order[payment.orderId] = payment

        if self._mongo_db is not None:
            try:
                self._mongo_db["payments"].update_one(
                    {"id": payment.id},
                    {"$set": payment.model_dump()},
                    upsert=True
                )
            except Exception as e:
                logger.warning(f"MongoDB payment write failed: {e}")

        logger.info(f"Payment recorded: {payment.id} for order '{payment.orderId}', status: {payment.paymentStatus.value}")
        return payment

    def get_payment_by_id(self, payment_id: str, user_id: Optional[str] = None) -> Optional[PaymentRecord]:
        p = self._payments.get(payment_id)
        if p and (user_id is None or p.userId == user_id):
            return p
        return None

    def get_payment_by_order(self, order_id: str, user_id: Optional[str] = None) -> Optional[PaymentRecord]:
        p = self._payments_by_order.get(order_id)
        if p and (user_id is None or p.userId == user_id):
            return p
        return None

    def get_user_payments(
        self,
        user_id: str,
        status: Optional[str] = None,
        transaction_type: Optional[str] = None,
        search: Optional[str] = None,
        sort_by: Optional[str] = "date_desc"
    ) -> List[PaymentRecord]:
        records = [p for p in self._payments.values() if p.userId == user_id]

        if status and status.upper() != "ALL":
            records = [p for p in records if p.paymentStatus.value.upper() == status.upper()]

        if transaction_type and transaction_type.upper() != "ALL":
            records = [p for p in records if p.transactionType.value.upper() == transaction_type.upper()]

        if search:
            q = search.lower().strip()
            records = [
                p for p in records
                if q in p.id.lower() or
                   q in p.orderId.lower() or
                   q in p.transactionId.lower() or
                   q in p.vehicleId.lower() or
                   q in p.paymentMethod.lower()
            ]

        if sort_by == "date_desc":
            records.sort(key=lambda x: x.createdAt, reverse=True)
        elif sort_by == "date_asc":
            records.sort(key=lambda x: x.createdAt)
        elif sort_by == "amount_desc":
            records.sort(key=lambda x: x.amount, reverse=True)
        elif sort_by == "amount_asc":
            records.sort(key=lambda x: x.amount)

        return records

    # -------------------------------------------------------------
    # PURCHASES & IDEMPOTENCY
    # -------------------------------------------------------------
    def record_purchase(
        self,
        order_id: str,
        transaction_reference: str,
        user_id: Optional[str] = None,
        payment_id: Optional[str] = None
    ) -> PurchaseRecord:
        """
        Creates an immutable, snapshot-backed purchase record.
        Strictly idempotent: retries/refreshes return the existing record.
        """
        if order_id in self._purchases_by_order:
            logger.info(f"Idempotency hit: Purchase for order '{order_id}' already recorded.")
            return self._purchases_by_order[order_id]

        target_user = user_id or self._demo_user_id

        # Retrieve order
        order = session_repo.get_order(order_id)
        if not order:
            order = PurchaseOrder(
                id=order_id,
                session_id=f"sess_{uuid.uuid4().hex[:6]}",
                vehicle_id="CAR-001",
                customer_name="Valued Customer",
                customer_email="customer@auramotors.com",
                customer_phone="+91 98765 43210",
                pan_or_id="ABCDE1234F",
                delivery_city="Delhi NCR",
                purchase_price=1450000.0,
                deposit_amount=25000.0,
                status=OrderStatus.CONFIRMED,
                payment_reference=transaction_reference,
                idempotency_key=f"idemp_{order_id}"
            )
            session_repo.create_order(order)

        # Retrieve vehicle for snapshot
        vehicle = marketplace_repo.get_vehicle_by_id(order.vehicle_id)
        if not vehicle:
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
            paymentId=payment_id or f"PAY-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
            orderId=order_id,
            vehicleSnapshot=snapshot,
            purchasePrice=order.purchase_price,
            depositAmount=order.deposit_amount,
            paymentStatus="SUCCESS",
            purchaseStatus=PurchaseStatus.CONFIRMED,
            purchaseDate=datetime.utcnow().isoformat() + "Z",
            transactionReference=transaction_reference,
            deliveryCity=order.delivery_city,
            demo_mode=True,
            createdAt=datetime.utcnow().isoformat() + "Z",
            updatedAt=datetime.utcnow().isoformat() + "Z"
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

    def get_purchase_by_id(self, purchase_id: str, user_id: Optional[str] = None) -> Optional[PurchaseRecord]:
        p = self._purchases.get(purchase_id)
        if p and (user_id is None or p.userId == user_id):
            return p
        return None

    def get_purchase_by_order(self, order_id: str) -> Optional[PurchaseRecord]:
        return self._purchases_by_order.get(order_id)

    # -------------------------------------------------------------
    # RENTALS & IDEMPOTENCY
    # -------------------------------------------------------------
    def record_rental(
        self,
        booking_id: str,
        transaction_reference: str,
        user_id: Optional[str] = None,
        payment_id: Optional[str] = None
    ) -> RentalRecord:
        """
        Creates an immutable, snapshot-backed rental record.
        Strictly idempotent: retries/refreshes return the existing record.
        """
        if booking_id in self._rentals_by_order:
            logger.info(f"Idempotency hit: Rental for booking '{booking_id}' already recorded.")
            return self._rentals_by_order[booking_id]

        target_user = user_id or self._demo_user_id

        booking = session_repo.get_booking(booking_id)
        vehicle = marketplace_repo.get_vehicle_by_id(booking.vehicle_id) if booking else None

        if not vehicle:
            snapshot = VehicleSnapshot(
                id=booking.vehicle_id if booking else "CAR-001",
                brand="Aura",
                model="Rental Fleet Unit",
                variant="Self-Drive",
                year=2024,
                category="Sedan",
                image="https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=800&q=80",
                transmission="Automatic",
                fuel_type="Petrol",
                location=booking.pickup_location if booking else "Delhi NCR"
            )
        else:
            img_val = (
                getattr(vehicle, "image_url", None)
                or (vehicle.images[0] if hasattr(vehicle, "images") and getattr(vehicle, "images") else None)
                or "https://images.unsplash.com/photo-1549399542-7e3f8b79c341?auto=format&fit=crop&w=800&q=80"
            )
            snapshot = VehicleSnapshot(
                id=vehicle.id,
                brand=vehicle.brand,
                model=vehicle.model,
                variant=getattr(vehicle, "variant", "Self-Drive Edition"),
                year=vehicle.year,
                category=vehicle.category.value if hasattr(vehicle.category, "value") else str(vehicle.category),
                image=img_val,
                transmission=vehicle.transmission.value if hasattr(vehicle.transmission, "value") else str(vehicle.transmission),
                fuel_type=vehicle.fuel_type.value if hasattr(vehicle.fuel_type, "value") else str(vehicle.fuel_type),
                location=vehicle.location,
                specs={
                    "seats": getattr(vehicle, "seats", 5),
                    "mileage_kmpl": getattr(vehicle, "mileage_kmpl", 18.0)
                }
            )

        rental_id = f"RNT-{datetime.utcnow().strftime('%Y')}-{uuid.uuid4().hex[:6].upper()}"
        rental = RentalRecord(
            id=rental_id,
            userId=target_user,
            vehicleId=booking.vehicle_id if booking else snapshot.id,
            paymentId=payment_id or f"PAY-{datetime.utcnow().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}",
            orderId=booking_id,
            vehicleSnapshot=snapshot,
            pickupDate=booking.pickup_date if booking else datetime.utcnow().strftime("%Y-%m-%d"),
            returnDate=booking.return_date if booking else datetime.utcnow().strftime("%Y-%m-%d"),
            durationDays=booking.duration_days if booking else 5,
            pickupLocation=booking.pickup_location if booking else "Delhi NCR",
            returnLocation=booking.return_location if booking else "Delhi NCR",
            dailyRentalPrice=booking.base_rate if booking else 3000.0,
            rentalAmount=booking.total_amount if booking else 18290.0,
            securityDeposit=5000.0,
            rentalStatus=RentalStatus.CONFIRMED,
            paymentStatus="SUCCESS",
            transactionReference=transaction_reference,
            createdAt=datetime.utcnow().isoformat() + "Z",
            updatedAt=datetime.utcnow().isoformat() + "Z"
        )

        self._rentals[rental.id] = rental
        self._rentals_by_order[booking_id] = rental

        if self._mongo_db is not None:
            try:
                self._mongo_db["rentals"].update_one(
                    {"orderId": booking_id},
                    {"$set": rental.model_dump()},
                    upsert=True
                )
            except Exception as e:
                logger.warning(f"MongoDB rental write failed: {e}")

        logger.info(f"Rental successfully recorded: {rental.id} for user '{target_user}'.")
        return rental

    def get_user_rentals(
        self,
        user_id: str,
        search: Optional[str] = None,
        status: Optional[str] = None
    ) -> List[RentalRecord]:
        records = [r for r in self._rentals.values() if r.userId == user_id]

        if status and status.upper() != "ALL":
            records = [r for r in records if r.rentalStatus.value.upper() == status.upper() or r.paymentStatus == status]

        if search:
            q = search.lower().strip()
            records = [
                r for r in records
                if q in r.vehicleSnapshot.brand.lower() or
                   q in r.vehicleSnapshot.model.lower() or
                   q in r.orderId.lower() or
                   q in r.id.lower() or
                   q in r.pickupLocation.lower()
            ]

        records.sort(key=lambda x: x.createdAt, reverse=True)
        return records

    def get_rental_by_id(self, rental_id: str, user_id: Optional[str] = None) -> Optional[RentalRecord]:
        r = self._rentals.get(rental_id)
        if r and (user_id is None or r.userId == user_id):
            return r
        return None

    def get_rental_by_order(self, order_id: str) -> Optional[RentalRecord]:
        return self._rentals_by_order.get(order_id)

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
    # DASHBOARD SUMMARY
    # -------------------------------------------------------------
    def get_dashboard_summary(self, user_id: str) -> Dict[str, Any]:
        """Returns real computed counts from persistent records."""
        purchases = self.get_user_purchases(user_id)
        rentals = self.get_user_rentals(user_id)
        payments = self.get_user_payments(user_id)
        owned = self.get_user_owned_vehicles(user_id)
        active_listings = [l for l in self.get_user_listings(user_id) if l.status == ListingStatus.ACTIVE]

        total_spent = sum(p.purchasePrice for p in purchases) + sum(r.rentalAmount for r in rentals)
        total_payment_volume = sum(p.amount for p in payments if p.paymentStatus == PaymentStatus.SUCCESS)

        return {
            "total_purchases": len(purchases),
            "total_rentals": len(rentals),
            "active_rentals": len([r for r in rentals if r.rentalStatus in [RentalStatus.CONFIRMED, RentalStatus.ACTIVE]]),
            "total_payments": len(payments),
            "vehicles_owned": len([v for v in owned if v.status != "Sold"]),
            "active_selling_listings": len(active_listings),
            "total_spent_inr": total_spent,
            "total_settled_payments_inr": total_payment_volume,
            "portfolio_valuation_inr": sum(v.currentEstimatedValue or 0 for v in owned)
        }

# Singleton instance
user_data_repo = UserDataRepository()
