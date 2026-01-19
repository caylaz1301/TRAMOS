from app.services.osticket_service import osticket_service
from app.schemas.ticket import CreateTicketRequest

# Test service directly
ticket_data = CreateTicketRequest(
    name="Test Driver",
    email="test@tramos.com",
    subject="Test Ticket",
    message="Testing osTicket API"
)

print("Testing osTicket service directly...")
result = osticket_service.create_ticket(ticket_data)
print(f"Success: {result.success}")
print(f"Ticket ID: {result.ticket_id}")
print(f"Message: {result.message}")
if result.error:
    print(f"Error: {result.error}")
