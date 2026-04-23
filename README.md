# RePart AI - AI-Driven Auto Parts Negotiation System
📌 Overview
RePart AI is an intelligent system that automates the process of finding, inquiring, negotiating, and purchasing automotive parts using an AI-powered conversational agent.
The system integrates marketing, AI interaction, backend processing, and inventory management into a single workflow.

🎯 Problem Statement
Customers face multiple challenges when purchasing auto parts:
Difficulty finding compatible parts
Lack of transparent pricing
No negotiation support
Time-consuming manual process

💡 Solution
RePart AI solves these problems by:
Capturing leads using Google Ads
Interacting via an AI voice agent
Checking inventory in real time
Negotiating prices automatically
Sending payment links via email

⚙️ System Workflow
1.User searches for auto parts on Google
2.Google Ads displays RePart AI ad
3.User clicks ad and lands on website
4.User fills form (Name, Phone, Email)
5.AI agent calls the customer
6.AI handles inquiry or purchase
7.AI negotiates and finalizes deal
8.Payment link sent via email
9.Inventory updated based on payment
10.Order is confirmed and shipped

🤖 AI Agent (Core Feature)
Built using Retell AI
Handles:
     Inquiry (availability & price range)
     Purchase (deal negotiation)
Natural conversational flow
Human-like negotiation capability

📢 Marketing Strategy

RePart AI uses:

Google Search Ads → targets high-intent users
Google Display Ads → increases visibility

Users are redirected to a landing page where leads are captured.


🗄️ Backend System

The system uses three main database tables:

1. Leads Table

Stores customer details and requests

2. Inventory Table

Stores parts, pricing, and stock

3. Order History Table

Stores order and payment details

🔒 Smart Inventory Mechanism
Selected item is moved to reserved stock
Reservation time: 30 minutes
Logic:
✅ Payment Success → Stock reduced
❌ Payment Failed → Stock restored

This prevents multiple users from purchasing the same item.

💳 Payment System
Payment link sent via email
Uses Stripe (planned integration)

⚠️ Note:
Real-time payment integration is part of future implementation.


🧰 Tech Stack
Frontend: React
Backend: FastAPI
AI Agent: Retell AI
Marketing: Google Ads
Payment: Stripe (planned)


🚀 Features
AI-driven conversational system
Real-time inquiry handling
Automated price negotiation
Lead-to-order conversion
Smart inventory tracking


⚠️ Limitations
No live payment integration yet
Inventory depends on dataset
Delivery system is conceptual

🔮 Future Enhancements
Real-time Stripe integration
Live inventory APIs
WhatsApp/SMS integration
Advanced AI negotiation models

👩‍💻 Author

Sarath Chandra Bhimineni 
Mounika Sai Yaganti
Afroz Mohd
Nandini Sharma
Montclair State University
