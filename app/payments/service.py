"""
CUSTOS Payment Gateway Service

Abstract payment gateway interface with Razorpay implementation.
"""

import hashlib
import hmac
import secrets
from abc import ABC, abstractmethod
from datetime import datetime, timezone, timedelta
from typing import Optional, List, Dict, Any, Tuple
from uuid import UUID

from sqlalchemy import select, func, and_
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import ResourceNotFoundError, ValidationError, PaymentError
from app.payments.models import (
    GatewayConfig, PaymentOrder, PaymentTransaction, PaymentRefund, WebhookEvent,
    PaymentGateway, PaymentStatus, PaymentMethod, RefundStatus,
)
from app.payments.schemas import (
    GatewayConfigCreate, GatewayConfigUpdate,
    PaymentOrderCreate, PaymentVerifyRequest, RefundCreate,
    PaymentStats,
)


def generate_order_number() -> str:
    """Generate unique order number."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = secrets.token_hex(3).upper()
    return f"ORD{timestamp}{random_part}"


def generate_transaction_id() -> str:
    """Generate unique transaction ID."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = secrets.token_hex(4).upper()
    return f"TXN{timestamp}{random_part}"


def generate_refund_id() -> str:
    """Generate unique refund ID."""
    timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
    random_part = secrets.token_hex(3).upper()
    return f"RFD{timestamp}{random_part}"


def format_amount(amount_paise: int, currency: str = "INR") -> str:
    """Format amount in paise to display string."""
    amount = amount_paise / 100
    if currency == "INR":
        return f"₹{amount:,.2f}"
    return f"{currency} {amount:,.2f}"


# ============================================
# Abstract Gateway Interface
# ============================================

class PaymentGatewayInterface(ABC):
    """Abstract interface for payment gateways."""
    
    @abstractmethod
    async def create_order(
        self,
        amount: int,  # In paise
        currency: str,
        receipt: str,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a payment order on the gateway."""
        pass
    
    @abstractmethod
    async def verify_payment(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> bool:
        """Verify payment signature."""
        pass
    
    @abstractmethod
    async def fetch_payment(self, payment_id: str) -> Dict[str, Any]:
        """Fetch payment details from gateway."""
        pass
    
    @abstractmethod
    async def create_refund(
        self,
        payment_id: str,
        amount: int,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create a refund."""
        pass
    
    @abstractmethod
    async def fetch_refund(self, refund_id: str) -> Dict[str, Any]:
        """Fetch refund details."""
        pass
    
    @abstractmethod
    def get_checkout_data(
        self,
        order_id: str,
        amount: int,
        currency: str,
        description: str,
        customer_name: str,
        customer_email: str,
        customer_phone: str,
    ) -> Dict[str, Any]:
        """Get data for client-side checkout integration."""
        pass


# ============================================
# Razorpay Implementation
# ============================================

class RazorpayGateway(PaymentGatewayInterface):
    """Razorpay payment gateway implementation."""
    
    def __init__(self, api_key: str, api_secret: str, is_sandbox: bool = True):
        self.api_key = api_key
        self.api_secret = api_secret
        self.is_sandbox = is_sandbox
        self.base_url = "https://api.razorpay.com/v1"
    
    async def create_order(
        self,
        amount: int,
        currency: str,
        receipt: str,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create Razorpay order."""
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/orders",
                auth=(self.api_key, self.api_secret),
                json={
                    "amount": amount,
                    "currency": currency,
                    "receipt": receipt,
                    "notes": notes or {},
                },
            )
            
            if response.status_code != 200:
                raise PaymentError(f"Failed to create order: {response.text}")
            
            return response.json()
    
    async def verify_payment(
        self,
        order_id: str,
        payment_id: str,
        signature: str,
    ) -> bool:
        """Verify Razorpay payment signature."""
        message = f"{order_id}|{payment_id}"
        expected_signature = hmac.new(
            self.api_secret.encode(),
            message.encode(),
            hashlib.sha256
        ).hexdigest()
        
        return hmac.compare_digest(signature, expected_signature)
    
    async def fetch_payment(self, payment_id: str) -> Dict[str, Any]:
        """Fetch payment from Razorpay."""
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/payments/{payment_id}",
                auth=(self.api_key, self.api_secret),
            )
            
            if response.status_code != 200:
                raise PaymentError(f"Failed to fetch payment: {response.text}")
            
            return response.json()
    
    async def create_refund(
        self,
        payment_id: str,
        amount: int,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Create Razorpay refund."""
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.base_url}/payments/{payment_id}/refund",
                auth=(self.api_key, self.api_secret),
                json={
                    "amount": amount,
                    "notes": notes or {},
                },
            )
            
            if response.status_code != 200:
                raise PaymentError(f"Failed to create refund: {response.text}")
            
            return response.json()
    
    async def fetch_refund(self, refund_id: str) -> Dict[str, Any]:
        """Fetch refund from Razorpay."""
        import httpx
        
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{self.base_url}/refunds/{refund_id}",
                auth=(self.api_key, self.api_secret),
            )
            
            if response.status_code != 200:
                raise PaymentError(f"Failed to fetch refund: {response.text}")
            
            return response.json()
    
    def get_checkout_data(
        self,
        order_id: str,
        amount: int,
        currency: str,
        description: str,
        customer_name: str,
        customer_email: str,
        customer_phone: str,
    ) -> Dict[str, Any]:
        """Get Razorpay checkout.js data."""
        return {
            "key": self.api_key,
            "order_id": order_id,
            "amount": amount,
            "currency": currency,
            "name": description,
            "prefill": {
                "name": customer_name,
                "email": customer_email,
                "contact": customer_phone,
            },
            "theme": {
                "color": "#3399cc",
            },
        }


# ============================================
# Manual Payment Handler
# ============================================

class ManualPaymentHandler:
    """Handler for manual payments (cash, cheque, bank transfer)."""
    
    async def record_payment(
        self,
        amount: int,
        method: PaymentMethod,
        reference: Optional[str] = None,
        notes: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Record a manual payment."""
        return {
            "payment_id": f"MANUAL_{secrets.token_hex(8).upper()}",
            "amount": amount,
            "method": method.value,
            "reference": reference,
            "notes": notes,
            "status": "captured",
        }


# ============================================
# Payment Service
# ============================================

class PaymentService:
    """Main payment service with gateway abstraction."""
    
    def __init__(self, session: AsyncSession, tenant_id: UUID):
        self.session = session
        self.tenant_id = tenant_id
        self._gateway_cache: Dict[PaymentGateway, PaymentGatewayInterface] = {}
    
    async def _get_gateway_config(
        self, 
        gateway: PaymentGateway,
    ) -> Optional[GatewayConfig]:
        """Get gateway configuration."""
        query = select(GatewayConfig).where(
            GatewayConfig.tenant_id == self.tenant_id,
            GatewayConfig.gateway == gateway,
            GatewayConfig.is_active == True,
            GatewayConfig.is_deleted == False,
        )
        result = await self.session.execute(query)
        return result.scalar_one_or_none()
    
    async def _get_gateway_client(
        self, 
        gateway: PaymentGateway,
    ) -> PaymentGatewayInterface:
        """Get gateway client with caching."""
        if gateway in self._gateway_cache:
            return self._gateway_cache[gateway]
        
        config = await self._get_gateway_config(gateway)
        if not config:
            raise PaymentError(f"Gateway {gateway.value} is not configured")
        
        if gateway == PaymentGateway.RAZORPAY:
            client = RazorpayGateway(
                api_key=config.api_key,
                api_secret=config.api_secret,
                is_sandbox=config.is_sandbox,
            )
        else:
            raise PaymentError(f"Gateway {gateway.value} is not supported")
        
        self._gateway_cache[gateway] = client
        return client
    
    # ========================================
    # Gateway Config Management
    # ========================================
    
    async def configure_gateway(
        self, 
        data: GatewayConfigCreate,
    ) -> GatewayConfig:
        """Configure a payment gateway."""
        # Check if already exists
        existing = await self._get_gateway_config(data.gateway)
        if existing:
            raise ValidationError(f"Gateway {data.gateway.value} already configured")
        
        config = GatewayConfig(
            tenant_id=self.tenant_id,
            **data.model_dump(),
        )
        self.session.add(config)
        await self.session.commit()
        await self.session.refresh(config)
        return config
    
    async def update_gateway_config(
        self,
        gateway: PaymentGateway,
        data: GatewayConfigUpdate,
    ) -> GatewayConfig:
        """Update gateway configuration."""
        config = await self._get_gateway_config(gateway)
        if not config:
            raise ResourceNotFoundError("GatewayConfig", gateway.value)
        
        update_data = data.model_dump(exclude_unset=True)
        for key, value in update_data.items():
            if value is not None:
                setattr(config, key, value)
        
        # Clear cache
        if gateway in self._gateway_cache:
            del self._gateway_cache[gateway]
        
        await self.session.commit()
        await self.session.refresh(config)
        return config
    
    async def list_gateway_configs(self) -> List[GatewayConfig]:
        """List all gateway configurations."""
        query = select(GatewayConfig).where(
            GatewayConfig.tenant_id == self.tenant_id,
            GatewayConfig.is_deleted == False,
        )
        result = await self.session.execute(query)
        return list(result.scalars().all())
    
    # ========================================
    # Payment Order Operations
    # ========================================
    
    async def create_order(
        self,
        data: PaymentOrderCreate,
        amount: int,  # From invoice
        customer_info: Dict[str, str],  # name, email, phone
    ) -> Tuple[PaymentOrder, Dict[str, Any]]:
        """Create a payment order."""
        order_number = generate_order_number()
        
        # Create order on gateway
        checkout_data = {}
        gateway_order_id = None
        
        if data.gateway != PaymentGateway.MANUAL:
            gateway = await self._get_gateway_client(data.gateway)
            gateway_response = await gateway.create_order(
                amount=amount,
                currency="INR",
                receipt=order_number,
                notes=data.notes,
            )
            gateway_order_id = gateway_response.get("id")
            
            # Get checkout data for client
            checkout_data = gateway.get_checkout_data(
                order_id=gateway_order_id,
                amount=amount,
                currency="INR",
                description=data.description or "Fee Payment",
                customer_name=customer_info.get("name", ""),
                customer_email=customer_info.get("email", ""),
                customer_phone=customer_info.get("phone", ""),
            )
        
        # Create local order
        order = PaymentOrder(
            tenant_id=self.tenant_id,
            order_number=order_number,
            invoice_id=data.invoice_id,
            student_id=data.student_id,
            parent_id=data.parent_id,
            amount=amount,
            currency="INR",
            gateway=data.gateway,
            gateway_order_id=gateway_order_id,
            status=PaymentStatus.INITIATED,
            expires_at=datetime.now(timezone.utc) + timedelta(hours=24),
            description=data.description,
            notes=data.notes,
        )
        
        self.session.add(order)
        await self.session.commit()
        await self.session.refresh(order)
        
        return order, checkout_data
    
    async def get_order(self, order_id: UUID) -> PaymentOrder:
        """Get payment order by ID."""
        query = select(PaymentOrder).where(
            PaymentOrder.tenant_id == self.tenant_id,
            PaymentOrder.id == order_id,
            PaymentOrder.is_deleted == False,
        )
        result = await self.session.execute(query)
        order = result.scalar_one_or_none()
        if not order:
            raise ResourceNotFoundError("PaymentOrder", str(order_id))
        return order
    
    async def get_order_by_number(self, order_number: str) -> PaymentOrder:
        """Get payment order by order number."""
        query = select(PaymentOrder).where(
            PaymentOrder.tenant_id == self.tenant_id,
            PaymentOrder.order_number == order_number,
            PaymentOrder.is_deleted == False,
        )
        result = await self.session.execute(query)
        order = result.scalar_one_or_none()
        if not order:
            raise ResourceNotFoundError("PaymentOrder", order_number)
        return order
    
    # ========================================
    # Payment Verification
    # ========================================
    
    async def verify_payment(
        self,
        data: PaymentVerifyRequest,
    ) -> PaymentTransaction:
        """Verify and record a successful payment."""
        order = await self.get_order(data.order_id)
        
        if order.status == PaymentStatus.SUCCESS:
            raise ValidationError("Order already paid")
        
        # Verify with gateway
        if order.gateway != PaymentGateway.MANUAL:
            gateway = await self._get_gateway_client(order.gateway)
            
            if data.gateway_signature:
                is_valid = await gateway.verify_payment(
                    order.gateway_order_id,
                    data.gateway_payment_id,
                    data.gateway_signature,
                )
                if not is_valid:
                    raise PaymentError("Invalid payment signature")
            
            # Fetch payment details
            payment_details = await gateway.fetch_payment(data.gateway_payment_id)
        else:
            payment_details = {"status": "captured"}
        
        # Create transaction
        transaction = PaymentTransaction(
            tenant_id=self.tenant_id,
            transaction_id=generate_transaction_id(),
            order_id=order.id,
            amount=order.amount,
            currency=order.currency,
            gateway=order.gateway,
            gateway_payment_id=data.gateway_payment_id,
            gateway_signature=data.gateway_signature,
            method=data.method,
            method_details=data.method_details,
            status=PaymentStatus.SUCCESS,
            initiated_at=order.created_at,
            completed_at=datetime.now(timezone.utc),
            gateway_response=payment_details,
        )
        
        # Update order status
        order.status = PaymentStatus.SUCCESS
        
        self.session.add(transaction)
        await self.session.commit()
        await self.session.refresh(transaction)
        
        return transaction
    
    async def record_failed_payment(
        self,
        order_id: UUID,
        error_code: str,
        error_message: str,
    ) -> PaymentTransaction:
        """Record a failed payment attempt."""
        order = await self.get_order(order_id)
        
        transaction = PaymentTransaction(
            tenant_id=self.tenant_id,
            transaction_id=generate_transaction_id(),
            order_id=order.id,
            amount=order.amount,
            currency=order.currency,
            gateway=order.gateway,
            status=PaymentStatus.FAILED,
            initiated_at=order.created_at,
            completed_at=datetime.now(timezone.utc),
            error_code=error_code,
            error_message=error_message,
        )
        
        self.session.add(transaction)
        await self.session.commit()
        await self.session.refresh(transaction)
        
        return transaction
    
    # ========================================
    # Refunds
    # ========================================
    
    async def create_refund(
        self,
        data: RefundCreate,
        initiated_by: UUID,
    ) -> PaymentRefund:
        """Create a refund for a transaction."""
        # Get transaction
        query = select(PaymentTransaction).where(
            PaymentTransaction.tenant_id == self.tenant_id,
            PaymentTransaction.id == data.transaction_id,
            PaymentTransaction.is_deleted == False,
        )
        result = await self.session.execute(query)
        transaction = result.scalar_one_or_none()
        
        if not transaction:
            raise ResourceNotFoundError("PaymentTransaction", str(data.transaction_id))
        
        if transaction.status != PaymentStatus.SUCCESS:
            raise ValidationError("Can only refund successful transactions")
        
        # Check refund amount
        existing_refunds = await self.session.execute(
            select(func.sum(PaymentRefund.amount)).where(
                PaymentRefund.transaction_id == transaction.id,
                PaymentRefund.status.in_([RefundStatus.COMPLETED, RefundStatus.PROCESSING]),
            )
        )
        total_refunded = existing_refunds.scalar() or 0
        
        if total_refunded + data.amount > transaction.amount:
            raise ValidationError("Refund amount exceeds remaining refundable amount")
        
        # Create refund on gateway
        gateway_refund_id = None
        if transaction.gateway != PaymentGateway.MANUAL:
            gateway = await self._get_gateway_client(transaction.gateway)
            refund_response = await gateway.create_refund(
                transaction.gateway_payment_id,
                data.amount,
                {"reason": data.reason},
            )
            gateway_refund_id = refund_response.get("id")
        
        # Create refund record
        refund = PaymentRefund(
            tenant_id=self.tenant_id,
            refund_id=generate_refund_id(),
            transaction_id=transaction.id,
            amount=data.amount,
            gateway_refund_id=gateway_refund_id,
            status=RefundStatus.PROCESSING,
            reason=data.reason,
            initiated_by=initiated_by,
        )
        
        self.session.add(refund)
        await self.session.commit()
        await self.session.refresh(refund)
        
        return refund
    
    # ========================================
    # Webhooks
    # ========================================
    
    async def process_webhook(
        self,
        gateway: PaymentGateway,
        event_id: str,
        event_type: str,
        payload: Dict[str, Any],
    ) -> WebhookEvent:
        """Process and store webhook event."""
        # Store webhook
        webhook = WebhookEvent(
            tenant_id=self.tenant_id,
            event_id=event_id,
            gateway=gateway,
            event_type=event_type,
            payload=payload,
        )
        self.session.add(webhook)
        
        # Process based on event type
        try:
            if event_type == "payment.captured":
                await self._handle_payment_captured(payload)
            elif event_type == "payment.failed":
                await self._handle_payment_failed(payload)
            elif event_type == "refund.processed":
                await self._handle_refund_processed(payload)
            
            webhook.is_processed = True
            webhook.processed_at = datetime.now(timezone.utc)
        except Exception as e:
            webhook.error_message = str(e)
        
        await self.session.commit()
        await self.session.refresh(webhook)
        
        return webhook
    
    async def _handle_payment_captured(self, payload: Dict[str, Any]) -> None:
        """Handle payment captured webhook."""
        payment = payload.get("payload", {}).get("payment", {}).get("entity", {})
        order_id = payment.get("order_id")
        payment_id = payment.get("id")
        
        if order_id:
            # Find order by gateway_order_id
            query = select(PaymentOrder).where(
                PaymentOrder.gateway_order_id == order_id,
            )
            result = await self.session.execute(query)
            order = result.scalar_one_or_none()
            
            if order and order.status != PaymentStatus.SUCCESS:
                order.status = PaymentStatus.SUCCESS
    
    async def _handle_payment_failed(self, payload: Dict[str, Any]) -> None:
        """Handle payment failed webhook."""
        payment = payload.get("payload", {}).get("payment", {}).get("entity", {})
        order_id = payment.get("order_id")
        
        if order_id:
            query = select(PaymentOrder).where(
                PaymentOrder.gateway_order_id == order_id,
            )
            result = await self.session.execute(query)
            order = result.scalar_one_or_none()
            
            if order:
                order.status = PaymentStatus.FAILED
    
    async def _handle_refund_processed(self, payload: Dict[str, Any]) -> None:
        """Handle refund processed webhook."""
        refund = payload.get("payload", {}).get("refund", {}).get("entity", {})
        refund_id = refund.get("id")
        
        if refund_id:
            query = select(PaymentRefund).where(
                PaymentRefund.gateway_refund_id == refund_id,
            )
            result = await self.session.execute(query)
            refund_record = result.scalar_one_or_none()
            
            if refund_record:
                refund_record.status = RefundStatus.COMPLETED
                refund_record.processed_at = datetime.now(timezone.utc)
    
    # ========================================
    # History & Stats
    # ========================================
    
    async def get_payment_history(
        self,
        student_id: Optional[UUID] = None,
        status: Optional[PaymentStatus] = None,
        page: int = 1,
        size: int = 20,
    ) -> Tuple[List[PaymentTransaction], int]:
        """Get payment transaction history."""
        query = select(PaymentTransaction).join(PaymentOrder).where(
            PaymentTransaction.tenant_id == self.tenant_id,
            PaymentTransaction.is_deleted == False,
        )
        
        if student_id:
            query = query.where(PaymentOrder.student_id == student_id)
        if status:
            query = query.where(PaymentTransaction.status == status)
        
        # Count
        count_query = select(func.count()).select_from(query.subquery())
        total = (await self.session.execute(count_query)).scalar() or 0
        
        # Paginate
        skip = (page - 1) * size
        query = query.order_by(
            PaymentTransaction.created_at.desc()
        ).offset(skip).limit(size)
        
        result = await self.session.execute(query)
        return list(result.scalars().all()), total
    
    async def get_stats(
        self,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None,
    ) -> PaymentStats:
        """Get payment statistics."""
        base_query = select(PaymentTransaction).where(
            PaymentTransaction.tenant_id == self.tenant_id,
            PaymentTransaction.is_deleted == False,
        )
        
        if start_date:
            base_query = base_query.where(PaymentTransaction.created_at >= start_date)
        if end_date:
            base_query = base_query.where(PaymentTransaction.created_at <= end_date)
        
        # Totals
        total = (await self.session.execute(
            select(func.count()).select_from(base_query.subquery())
        )).scalar() or 0
        
        successful = (await self.session.execute(
            select(func.count()).select_from(
                base_query.where(PaymentTransaction.status == PaymentStatus.SUCCESS).subquery()
            )
        )).scalar() or 0
        
        failed = (await self.session.execute(
            select(func.count()).select_from(
                base_query.where(PaymentTransaction.status == PaymentStatus.FAILED).subquery()
            )
        )).scalar() or 0
        
        pending = (await self.session.execute(
            select(func.count()).select_from(
                base_query.where(PaymentTransaction.status == PaymentStatus.PENDING).subquery()
            )
        )).scalar() or 0
        
        # Amount collected
        collected = (await self.session.execute(
            select(func.sum(PaymentTransaction.amount)).where(
                PaymentTransaction.tenant_id == self.tenant_id,
                PaymentTransaction.status == PaymentStatus.SUCCESS,
            )
        )).scalar() or 0
        
        # Refunds
        refund_count = (await self.session.execute(
            select(func.count()).where(
                PaymentRefund.tenant_id == self.tenant_id,
                PaymentRefund.status == RefundStatus.COMPLETED,
            )
        )).scalar() or 0
        
        refund_amount = (await self.session.execute(
            select(func.sum(PaymentRefund.amount)).where(
                PaymentRefund.tenant_id == self.tenant_id,
                PaymentRefund.status == RefundStatus.COMPLETED,
            )
        )).scalar() or 0
        
        return PaymentStats(
            total_transactions=total,
            successful_transactions=successful,
            failed_transactions=failed,
            pending_transactions=pending,
            total_amount_collected=collected,
            total_amount_collected_display=format_amount(collected),
            total_refunds=refund_count,
            total_refund_amount=refund_amount,
            total_refund_amount_display=format_amount(refund_amount),
            by_gateway={},
            by_method={},
            daily_collections=[],
        )
