"""
Realistic Sample Email Dataset for Travel Ingestion.
Contains flights, trains, buses, hotels, and activities, including
clean standard confirmations and imperfect/ambiguous forwards.
"""

SAMPLE_EMAILS = [
    {
        "id": "flight-indigo-6e",
        "category": "flight",
        "title": "IndiGo 6E-205 Mumbai to Delhi Confirmation",
        "sender": "reservations@goindigo.in",
        "subject": "Booking Confirmation - 6E 205 (PNR: 6E-IND789)",
        "body": """
Dear Traveler Sahil Sharma,

Thank you for choosing IndiGo. Your flight booking is confirmed!

Booking Reference (PNR): 6E-IND789
Passenger: Sahil Sharma
Status: Confirmed

Flight Details:
- Flight: IndiGo 6E-205 (Airbus A321neo)
- Origin: Mumbai (BOM) - Chhatrapati Shivaji Maharaj Intl, Terminal 2
- Destination: Delhi (DEL) - Indira Gandhi Intl, Terminal 3
- Departure: 2026-10-20T08:30:00
- Arrival: 2026-10-20T10:45:00
- Seat: 12F
- Baggage: 15kg check-in, 7kg cabin

Total Fare Paid: INR 5,850.00
Payment Method: UPI / Credit Card

Have a pleasant journey!
IndiGo Airlines
""",
        "is_imperfect": False,
        "expected_type": "flight"
    },
    {
        "id": "train-irctc-rajdhani",
        "category": "train",
        "title": "IRCTC Rajdhani Express E-Ticket Confirmation",
        "sender": "ticketadmin@irctc.co.in",
        "subject": "Electronic Reservation Slip (ERS) - PNR: 2458901234",
        "body": """
INDIAN RAILWAYS CATERING AND TOURISM CORPORATION LTD.
Booking Confirmation - E-Ticket

PNR Number: 2458901234
Train Number & Name: 12951 / Mumbai Central Tejas Rajdhani Express
Class: AC 2 Tier (2A)
Quotas: General

From Station: Mumbai Central (MMCT)
To Station: New Delhi (NDLS)
Date of Journey: 2026-10-22T17:00:00
Scheduled Arrival: 2026-10-23T08:32:00

Passenger Details:
1. Sahil Sharma | Male | 30 Yrs | Coach: B3 | Seat/Berth: 42 (Lower Berth)

Total Fare: INR 3,420.00
IRCTC Service Charge: INR 35.40

Wish you a happy and comfortable journey.
IRCTC Team
""",
        "is_imperfect": False,
        "expected_type": "train"
    },
    {
        "id": "hotel-marriott-mumbai",
        "category": "hotel",
        "title": "JW Marriott Mumbai Sahar Reservation Confirmation",
        "sender": "reservations@marriott.com",
        "subject": "Reservation Confirmed: JW Marriott Mumbai Sahar #92834110",
        "body": """
MARRIOTT BONVOY - RESERVATION CONFIRMATION

Dear Sahil Sharma,

We are delighted to confirm your upcoming stay with us.

Confirmation Number: 92834110
Hotel: JW Marriott Mumbai Sahar
Location: IA Project Road, Chhatrapati Shivaji Airport, Mumbai, Maharashtra 400099
Phone: +91 22 6882 8888

Dates of Stay:
- Check-in: 2026-10-18T15:00:00
- Check-out: 2026-10-20T12:00:00
- Number of Nights: 2 Nights

Room Details:
- 1 Deluxe Guest room, 1 King bed, Airport view
- Rate: INR 14,500.00 per night
- Total Estimated Taxes & Fees Included: INR 34,220.00

Cancellation Policy: Cancel up to 24 hours prior to arrival with no penalty.
We look forward to welcoming you.

Warm regards,
JW Marriott Team
""",
        "is_imperfect": False,
        "expected_type": "hotel"
    },
    {
        "id": "bus-redbus-express",
        "category": "bus",
        "title": "redBus Intercity Volvo AC Bus Booking",
        "sender": "tickets@redbus.in",
        "subject": "redBus Ticket Confirmation - Ticket No: TIN-9823487",
        "body": """
redBus Booking Confirmation

Ticket Number: TIN-9823487
Operator: Zingbus Electric AC Sleeper (2+1)
Passenger: Sahil Sharma

Travel Schedule:
- Boarding Point: Kashmere Gate ISBT, Delhi
- Drop-off Point: Sector 43 ISBT, Chandigarh
- Departure: 2026-10-24T06:00:00
- Arrival: 2026-10-24T11:15:00
- Seat Number: 14UB

Total Amount Paid: INR 850.00
Reporting Time: Please arrive 15 minutes prior to departure.

Customer Support: support@redbus.in
""",
        "is_imperfect": False,
        "expected_type": "bus"
    },
    {
        "id": "activity-getyourguide-tour",
        "category": "activity",
        "title": "GetYourGuide Old Delhi Heritage & Street Food Tour",
        "sender": "bookings@getyourguide.com",
        "subject": "Your booking for Old Delhi Guided Heritage Walk (Ref: GYG-77412)",
        "body": """
GetYourGuide - Booking Voucher

Activity: Old Delhi Street Food & Heritage Walking Tour
Booking Reference: GYG-77412
Lead Traveler: Sahil Sharma
Provider: Delhi Magic Walks & Tours

Tour Schedule:
- Meeting Point: Jama Masjid Gate No. 3, Delhi
- Tour Date & Start Time: 2026-10-21T16:00:00
- End Time: 2026-10-21T19:30:00
- Duration: 3.5 hours
- Group Size: 1 Adult

Price: USD 35.00
Voucher Status: Confirmed & Paid

Please present this voucher upon meeting your guide.
""",
        "is_imperfect": False,
        "expected_type": "activity"
    },
    {
        "id": "imperfect-flight-forward",
        "category": "flight",
        "title": "Imperfect Forwarded Flight Note (Missing Flight # & Times)",
        "sender": "traveler@gmail.com",
        "subject": "Fwd: My Air India flight next month",
        "body": """
---------- Forwarded message ---------
Hey team, here is my Air India booking reference: AI-REF90021.
I'm flying out from Mumbai to Singapore on the 28th of October, but I can't find the exact flight number or timing on this receipt.
Passenger name is Sahil Sharma.
Can you please link this to my journey?
Thanks!
""",
        "is_imperfect": True,
        "expected_type": "flight"
    },
    {
        "id": "imperfect-hotel-forward",
        "category": "hotel",
        "title": "Imperfect Hotel Receipt (Ambiguous Check-in & Dates)",
        "sender": "colleague@acme.corp",
        "subject": "Fwd: Stay in Bengaluru booked",
        "body": """
Hi,
I booked Taj MG Road Bengaluru under reference TAJ-5512 for you.
Check-in is on October 25th, but we still need to confirm whether checkout is the 27th or 28th with accounts.
Total paid: INR 18,000.
""",
        "is_imperfect": True,
        "expected_type": "hotel"
    }
]
