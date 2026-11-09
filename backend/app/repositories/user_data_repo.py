import uuid
import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from ..models.payment import PaymentRecord, PaymentStatus, TransactionType
from ..models.purchase import PurchaseRecord, VehicleSnapshot, PurchaseStatus
from ..models.listing import VehicleListing, ListingStatus, ApprovalStatus
from ..models.order import PurchaseOrder, OrderStatus
from ..repositories.marketplace import marketplace_repo
from ..repositories.session import session_repo
from ..config import settings
from ..db.mongodb import mongodb_manager

logger = logging.getLogger("car_consultant.user_data")

class UserDataRepository:
    def __init__(self):
        self._payments: Dict[str, PaymentRecord] = {}
        self._payments_by_order: Dict[str, PaymentRecord] = {}
        self._payments_by_idemp: Dict[str, PaymentRecord] = {}
        self._purchases: Dict[str, PurchaseRecord] = {}
        self._purchases_by_order: Dict[str, PurchaseRecord] = {}
        self._listings: Dict[str, VehicleListing] = {}
        self._demo_user_id = "usr_demo_01"
        self._init_mongo()
        self._seed_initial_demo_data()

    def _init_mongo(self):
        """Attempt MongoDB connection if available."""
        try:
            if not mongodb_manager.is_connected():
                mongodb_manager.connect()
            if mongodb_manager.is_connected():
                db = mongodb_manager.get_database()
                logger.info(f"UserDataRepository linked to MongoDB database '{db.name if db else 'unknown'}'.")
                self._load_from_mongo()
        except Exception as e:
            logger.info(f"MongoDB initialization notice: {e}. Operating with in-memory persistence layer.")

    def _load_from_mongo(self):
        """Loads persistent purchases, payments, and listings from MongoDB Atlas."""
        db = mongodb_manager.get_database()
        if db is None:
            return
        try:
            # 1. Purchases
            p_coll = db["purchases"]
            for doc in p_coll.find({}, {"_id": 0}):
                p = PurchaseRecord(**doc)
                self._purchases[p.id] = p
                self._purchases_by_order[p.orderId] = p

            # 2. Payments
            pay_coll = db["payments"]
            for doc in pay_coll.find({}, {"_id": 0}):
                pay = PaymentRecord(**doc)
                self._payments[pay.id] = pay
                self._payments_by_order[pay.orderId] = pay
                if pay.idempotencyKey:
                    self._payments_by_idemp[pay.idempotencyKey] = pay

            # 3. Listings
            l_coll = db["selling_listings"]
            for doc in l_coll.find({}, {"_id": 0}):
                listing = VehicleListing(**doc)
                self._listings[listing.id] = listing
        except Exception as e:
            logger.warning(f"Error loading records from MongoDB Atlas: {e}")

    def _seed_initial_demo_data(self):
        """Seeds initial verified portfolio for demo user 'usr_demo_01' if empty."""
        if not self._listings:
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

        if not self._purchases:
            # Verified purchase order for demo user
            init_order_id = "ORD-2026-DEMO-001"
            init_snapshot = VehicleSnapshot(
                id="CAR-001",
                brand="Hyundai",
                model="Creta SX (O) Turbo",
                variant="1.5L Turbo DCT Automatic",
                year=2024,
                category="SUV",
                image="https://images.unsplash.com/photo-1533473359331-0135ef1b58bf?auto=format&fit=crop&w=800&q=80",
                transmission="Automatic",
                fuel_type="Petrol",
                location="Delhi NCR",
                specs={
                    "mileage_kmpl": 18.2,
                    "power_bhp": 158,
                    "seats": 5,
                    "condition": "new"
                }
            )
            init_purchase = PurchaseRecord(
                id="PUR-2026-001",
                userId=self._demo_user_id,
                vehicleId="CAR-001",
                paymentId="PAY-20261101-001",
                orderId=init_order_id,
                vehicleSnapshot=init_snapshot,
                purchasePrice=2015000.0,
                depositAmount=25000.0,
                paymentStatus="SUCCESS",
                purchaseStatus=PurchaseStatus.CONFIRMED,
                purchaseDate="2026-11-01T10:15:00Z",
                transactionReference="TXN-AURA-98712345",
                deliveryCity="Delhi NCR",
                demo_mode=True,
                createdAt="2026-11-01T10:15:00Z",
                updatedAt="2026-11-01T10:15:00Z"
            )
            self._purchases[init_purchase.id] = init_purchase
            self._purchases_by_order[init_order_id] = init_purchase

            init_payment = PaymentRecord(
                id="PAY-20261101-001",
                userId=self._demo_user_id,
                orderId=init_order_id,
                transactionId="TXN-AURA-98712345",
                vehicleId="CAR-001",
                transactionType=TransactionType.BUY,
                amount=25000.0,
                currency="INR",
                paymentMethod="UPI",
                paymentStatus=PaymentStatus.SUCCESS,
                paymentProvider="MOCK_PAYMENT",
                paymentReference="TXN-AURA-98712345",
                idempotencyKey="idemp_init_order_001",
                createdAt="2026-11-01T10:15:00Z",
                updatedAt="2026-11-01T10:15:00Z"
            )
            self._payments[init_payment.id] = init_payment
            self._payments_by_order[init_order_id] = init_payment
            self._payments_by_idemp[init_payment.idempotencyKey] = init_payment

    # -------------------------------------------------------------
    # PAYMENTS & IDEMPOTENCY
    # -------------------------------------------------------------
    def record_payment(
        self,
        payment: PaymentRecord,
        idempotency_key: Optional[str] = None
    ) -> PaymentRecord:
        """Stores payment record in MongoDB Atlas and in-memory cache."""
        if idempotency_key:
            if idempotency_key in self._payments_by_idemp:
                logger.info(f"Idempotency hit: Payment for key '{idempotency_key}' already recorded.")
                return self._payments_by_idemp[idempotency_key]
            self._payments_by_idemp[idempotency_key] = payment

        self._payments[payment.id] = payment
        self._payments_by_order[payment.orderId] = payment

        db = mongodb_manager.get_database()
        if db is not None:
            try:
                db["payments"].update_one(
                    {"id": payment.id},
                    {"$set": payment.model_dump()},
                    upsert=True
                )
            except Exception as e:
                logger.warning(f"MongoDB payment write failed: {e}")

        logger.info(f"Payment recorded: {payment.id} for order '{payment.orderId}', status: {payment.paymentStatus.value}")
        return payment

    def get_payment_by_id(self, payment_id: str, user_id: Optional[str] = None) -> Optional[PaymentRecord]:
        db = mongodb_manager.get_database()
        if db is not None:
            try:
                query = {"id": payment_id}
                if user_id:
                    query["userId"] = user_id
                doc = db["payments"].find_one(query, {"_id": 0})
                if doc:
                    return PaymentRecord(**doc)
            except Exception:
                pass
        p = self._payments.get(payment_id)
        if p and (user_id is None or p.userId == user_id):
            return p
        return None

    def get_payment_by_order(self, order_id: str, user_id: Optional[str] = None) -> Optional[PaymentRecord]:
        db = mongodb_manager.get_database()
        if db is not None:
            try:
                query = {"orderId": order_id}
                if user_id:
                    query["userId"] = user_id
                doc = db["payments"].find_one(query, {"_id": 0})
                if doc:
                    return PaymentRecord(**doc)
            except Exception:
                pass
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
        db = mongodb_manager.get_database()
        records: List[PaymentRecord] = []
        if db is not None:
            try:
                query: Dict[str, Any] = {"userId": user_id}
                if status and status.upper() != "ALL":
                    query["paymentStatus"] = status.upper()
                if transaction_type and transaction_type.upper() != "ALL":
                    query["transactionType"] = transaction_type.upper()
                docs = list(db["payments"].find(query, {"_id": 0}))
                records = [PaymentRecord(**d) for d in docs]
            except Exception:
                records = []

        if not records:
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
        Creates an immutable, snapshot-backed purchase record in MongoDB Atlas.
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

        # Sync to MongoDB Atlas collection "purchases" and "orders"
        db = mongodb_manager.get_database()
        if db is not None:
            try:
                db["purchases"].update_one(
                    {"orderId": order_id},
                    {"$set": purchase.model_dump()},
                    upsert=True
                )
                db["orders"].update_one(
                    {"id": order.id},
                    {"$set": order.model_dump()},
                    upsert=True
                )
            except Exception as e:
                logger.warning(f"MongoDB purchase write failed: {e}")

        logger.info(f"Purchase successfully recorded: {purchase.id} for user '{target_user}'.")
        return purchase

    def get_user_owned_vehicles(self, user_id: str) -> List[Any]:
        """Maps user confirmed purchases to owned vehicle representations."""
        purchases = self.get_user_purchases(user_id)
        owned_list = []
        for p in purchases:
            snap = p.vehicleSnapshot
            class OwnedVehicleItem:
                def __init__(self, p_rec, s):
                    self.id = s.id or p_rec.vehicleId
                    self.brand = s.brand
                    self.model = s.model
                    self.variant = s.variant or "Standard Edition"
                    self.year = s.year or 2024
                    self.category = s.category
                    self.image = s.image
                    self.purchasePrice = p_rec.purchasePrice
                    self.currentEstimatedValue = round(p_rec.purchasePrice * 0.9, 2)
            owned_list.append(OwnedVehicleItem(p, snap))
        return owned_list

    def get_user_purchases(
        self,
        user_id: str,
        search: Optional[str] = None,
        sort_by: Optional[str] = "date_desc",
        status: Optional[str] = None
    ) -> List[PurchaseRecord]:
        db = mongodb_manager.get_database()
        records: List[PurchaseRecord] = []
        if db is not None:
            try:
                query: Dict[str, Any] = {"userId": user_id}
                if status and status.upper() != "ALL":
                    query["purchaseStatus"] = status.upper()
                docs = list(db["purchases"].find(query, {"_id": 0}))
                records = [PurchaseRecord(**d) for d in docs]
            except Exception:
                records = []

        if not records:
            records = [p for p in self._purchases.values() if p.userId == user_id]
            if status and status.upper() != "ALL":
                records = [p for p in records if p.purchaseStatus.value == status or p.paymentStatus == status]

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
        db = mongodb_manager.get_database()
        if db is not None:
            try:
                query = {"id": purchase_id}
                if user_id:
                    query["userId"] = user_id
                doc = db["purchases"].find_one(query, {"_id": 0})
                if doc:
                    return PurchaseRecord(**doc)
            except Exception:
                pass
        p = self._purchases.get(purchase_id)
        if p and (user_id is None or p.userId == user_id):
            return p
        return None

    def get_purchase_by_order(self, order_id: str) -> Optional[PurchaseRecord]:
        db = mongodb_manager.get_database()
        if db is not None:
            try:
                doc = db["purchases"].find_one({"orderId": order_id}, {"_id": 0})
                if doc:
                    return PurchaseRecord(**doc)
            except Exception:
                pass
        return self._purchases_by_order.get(order_id)

    # -------------------------------------------------------------
    # VEHICLE LISTINGS (SELL A CAR)
    # -------------------------------------------------------------
    def create_listing(self, listing: VehicleListing) -> VehicleListing:
        self._listings[listing.id] = listing

        db = mongodb_manager.get_database()
        if db is not None:
            try:
                db["selling_listings"].update_one(
                    {"id": listing.id},
                    {"$set": listing.model_dump()},
                    upsert=True
                )
            except Exception as e:
                logger.warning(f"MongoDB listing write failed: {e}")

        logger.info(f"Listing created: {listing.id} for seller '{listing.sellerId}'.")
        return listing

    def get_user_listings(self, user_id: str, status: Optional[str] = None) -> List[VehicleListing]:
        db = mongodb_manager.get_database()
        records: List[VehicleListing] = []
        if db is not None:
            try:
                query: Dict[str, Any] = {"sellerId": user_id}
                if status and status.lower() != "all":
                    query["status"] = status.lower()
                docs = list(db["selling_listings"].find(query, {"_id": 0}))
                records = [VehicleListing(**d) for d in docs]
            except Exception:
                records = []

        if not records:
            records = [l for l in self._listings.values() if l.sellerId == user_id]
            if status and status.lower() != "all":
                records = [l for l in records if l.status.value.lower() == status.lower()]

        records.sort(key=lambda x: x.created_at, reverse=True)
        return records

    def get_listing_by_id(self, listing_id: str, user_id: Optional[str] = None) -> Optional[VehicleListing]:
        db = mongodb_manager.get_database()
        if db is not None:
            try:
                query = {"id": listing_id}
                if user_id:
                    query["sellerId"] = user_id
                doc = db["selling_listings"].find_one(query, {"_id": 0})
                if doc:
                    return VehicleListing(**doc)
            except Exception:
                pass
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

        db = mongodb_manager.get_database()
        if db is not None:
            try:
                db["selling_listings"].update_one(
                    {"id": listing_id},
                    {"$set": l.model_dump()},
                    upsert=True
                )
            except Exception:
                pass
        return l

    def delete_listing(self, listing_id: str, user_id: str) -> bool:
        l = self.get_listing_by_id(listing_id, user_id)
        if not l:
            return False
        l.status = ListingStatus.REMOVED
        l.updated_at = datetime.utcnow().isoformat() + "Z"
        self._listings[listing_id] = l

        db = mongodb_manager.get_database()
        if db is not None:
            try:
                db["selling_listings"].update_one(
                    {"id": listing_id},
                    {"$set": {"status": "removed", "updated_at": l.updated_at}}
                )
            except Exception:
                pass
        return True

    # -------------------------------------------------------------
    # DASHBOARD SUMMARY
    # -------------------------------------------------------------
    def get_dashboard_summary(self, user_id: str) -> Dict[str, Any]:
        """Returns computed metrics exclusively for purchases, payments, listings, and saved cars."""
        purchases = self.get_user_purchases(user_id)
        payments = self.get_user_payments(user_id)
        active_listings = [l for l in self.get_user_listings(user_id) if l.status == ListingStatus.ACTIVE]
        saved_ids = self.get_saved_vehicle_ids(user_id)

        total_spent = sum(p.purchasePrice for p in purchases)
        total_payment_volume = sum(p.amount for p in payments if p.paymentStatus == PaymentStatus.SUCCESS)

        return {
            "total_purchases": len(purchases),
            "total_spent_inr": total_spent,
            "total_payments": len(payments),
            "total_settled_payments_inr": total_payment_volume,
            "active_selling_listings": len(active_listings),
            "total_saved": len(saved_ids)
        }

    def get_profile(self, user_id: Optional[str] = None) -> Optional[Dict[str, Any]]:
        from ..api.routes_auth import find_user_by_id, find_user_by_email
        target_id = user_id or self._demo_user_id
        u = find_user_by_id(target_id)
        if u:
            return {k: v for k, v in u.items() if k != "password_hash"}
        return {
            "id": "usr_demo_01",
            "name": "Alex Vance",
            "email": "demo@auramotors.com",
            "phone": "+91 98765 43210",
            "saved_vehicles": ["CAR-001", "CAR-021"]
        }

    def get_all_purchases(self) -> List[PurchaseRecord]:
        return list(self._purchases.values())

    def get_all_payments(self) -> List[PaymentRecord]:
        return list(self._payments.values())

    def get_all_selling_listings(self) -> List[VehicleListing]:
        return list(self._listings.values())

    def get_saved_vehicle_ids(self, user_id: Optional[str] = None) -> List[str]:
        p = self.get_profile(user_id)
        return p.get("saved_vehicles", []) if p else []

# Singleton instance
user_data_repo = UserDataRepository()
