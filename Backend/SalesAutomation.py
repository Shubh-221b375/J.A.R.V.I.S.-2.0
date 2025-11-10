"""
Sales Automation Functions
Provides sales-specific automation capabilities including pitch generation,
follow-up emails, WhatsApp outreach, lead analysis, and CRM integration
"""

import json
import os
from datetime import datetime, timedelta
from typing import Dict, Any, List, Optional
from dotenv import dotenv_values
from groq import Groq

# Import sales memory functions
from Backend.SalesMemory import sales_memory_manager, recall_memory, get_sales_knowledge

env_vars = dotenv_values(".env")
GroqAPIKey = env_vars.get("GroqAPIKey")
Username = env_vars.get("Username", "Sales Team")
Assistantname = env_vars.get("Assistantname", "Sales Assistant")

# Initialize Groq client
client = None
if GroqAPIKey:
    try:
        client = Groq(api_key=GroqAPIKey)
    except Exception as e:
        print(f"Error initializing Groq client in SalesAutomation: {e}")

# Sales system prompt
SALES_SYSTEM_PROMPT = f"""You are a professional sales AI assistant named {Assistantname}.
Your role is to help with sales activities including:
- Generating personalized sales pitches
- Creating follow-up emails
- Analyzing lead data and suggesting strategies
- Providing sales insights based on stored knowledge

Your tone should be:
- Friendly, professional, and persuasive
- Confident and motivating
- Clear and concise
- Focused on building relationships and closing deals

Always provide actionable sales advice and personalized content."""

def generate_sales_pitch(
    lead_name: str,
    company_name: str,
    product_or_service: str,
    context: Optional[str] = None
) -> str:
    """
    Generate a personalized sales pitch for a lead
    
    Args:
        lead_name: Name of the lead
        company_name: Company name
        product_or_service: Product or service to pitch
        context: Optional additional context about the lead
        
    Returns:
        Generated sales pitch text
    """
    if not client:
        return f"Hello {lead_name}, I'd like to introduce you to {product_or_service} which could benefit {company_name}."
    
    # Recall relevant knowledge about the lead/product
    knowledge_context = ""
    if lead_name or company_name:
        query = f"{lead_name} {company_name} {product_or_service}"
        relevant_memories = recall_memory(query, top_k=3, category="lead")
        if relevant_memories:
            knowledge_context = "\n\nRelevant Lead Information:\n"
            for mem in relevant_memories:
                knowledge_context += f"- {mem.get('content', '')}\n"
    
    prompt = f"""Generate a personalized sales pitch for:
- Lead Name: {lead_name}
- Company: {company_name}
- Product/Service: {product_or_service}
{f'- Context: {context}' if context else ''}

{knowledge_context}

Create a compelling, personalized sales pitch that:
1. Addresses the lead by name
2. Highlights relevant benefits for their company
3. Creates urgency and value proposition
4. Includes a clear call-to-action
5. Is friendly, professional, and persuasive

Keep the pitch concise (2-3 paragraphs maximum)."""
    
    try:
        # Try multiple models for reliability
        models_to_try = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
        completion = None
        
        for model in models_to_try:
            try:
                completion = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SALES_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=500,
                    temperature=0.8
                )
                break
            except Exception as model_error:
                if model == models_to_try[-1]:  # Last model failed
                    raise model_error
                continue
        
        if completion:
            pitch = completion.choices[0].message.content
            return pitch
        else:
            raise Exception("All models failed")
    except Exception as e:
        print(f"Error generating sales pitch: {e}")
        # Fallback pitch
        return f"""Hello {lead_name},

I hope this message finds you well. I wanted to reach out regarding {product_or_service}, which I believe could significantly benefit {company_name}.

[Your personalized value proposition would go here based on stored knowledge]

I'd love to schedule a brief call to discuss how this could help your organization. Would you be available for a 15-minute conversation this week?

Best regards,
{Username}"""

def send_followup_email(
    lead_name: str,
    lead_email: str,
    previous_interaction: Optional[str] = None,
    days_since_contact: int = 3,
    purpose: str = "general"
) -> Dict[str, Any]:
    """
    Generate and prepare a follow-up email
    
    Args:
        lead_name: Name of the lead
        lead_email: Email address
        previous_interaction: Notes about previous interaction
        days_since_contact: Days since last contact
        purpose: Purpose of follow-up (general, proposal, demo, closing)
        
    Returns:
        Dictionary with email content and metadata
    """
    if not client:
        return {
            "success": False,
            "error": "AI client not available"
        }
    
    # Get relevant knowledge about the lead
    knowledge = get_sales_knowledge(f"{lead_name} {lead_email}", category="lead")
    
    purpose_templates = {
        "general": "a friendly follow-up",
        "proposal": "to follow up on the proposal we sent",
        "demo": "to schedule a product demonstration",
        "closing": "to finalize the deal"
    }
    
    purpose_text = purpose_templates.get(purpose, "a follow-up")
    
    prompt = f"""Generate a professional follow-up email for:
- Lead Name: {lead_name}
- Days since last contact: {days_since_contact}
- Purpose: {purpose_text}
- Previous interaction: {previous_interaction or 'Initial contact'}

{knowledge}

Create a follow-up email that:
1. References previous interaction (if any)
2. Adds value (insight, resource, update)
3. Has a clear next step/call-to-action
4. Is friendly and professional
5. Creates gentle urgency if appropriate

Format: Subject line and email body."""
    
    try:
        # Try multiple models for reliability
        models_to_try = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
        completion = None
        
        for model in models_to_try:
            try:
                completion = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SALES_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=600,
                    temperature=0.7
                )
                break
            except Exception as model_error:
                if model == models_to_try[-1]:  # Last model failed
                    raise model_error
                continue
        
        if not completion:
            raise Exception("All models failed")
        
        email_content = completion.choices[0].message.content
        
        # Parse subject and body
        lines = email_content.split('\n')
        subject = ""
        body = ""
        
        if lines[0].startswith("Subject:"):
            subject = lines[0].replace("Subject:", "").strip()
            body = "\n".join(lines[1:]).strip()
        else:
            subject = f"Following up - {lead_name}"
            body = email_content
        
        email_data = {
            "success": True,
            "to": lead_email,
            "subject": subject,
            "body": body,
            "lead_name": lead_name,
            "purpose": purpose,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store email in memory for tracking
        sales_memory_manager.add_knowledge(
            f"Follow-up email sent to {lead_name} ({lead_email}): {subject}",
            "email_log",
            "communication",
            metadata=email_data
        )
        
        return email_data
    
    except Exception as e:
        print(f"Error generating follow-up email: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def whatsapp_outreach(
    lead_name: str,
    phone_number: str,
    message_type: str = "intro",
    product_or_service: Optional[str] = None
) -> Dict[str, Any]:
    """
    Generate WhatsApp message for lead outreach
    
    Args:
        lead_name: Name of the lead
        phone_number: Phone number (with country code)
        message_type: Type of message (intro, followup, closing)
        product_or_service: Product or service to mention
        
    Returns:
        Dictionary with message content and metadata
    """
    if not client:
        return {
            "success": False,
            "error": "AI client not available"
        }
    
    # Get relevant knowledge
    knowledge = get_sales_knowledge(f"{lead_name}", category="lead")
    
    message_types = {
        "intro": "an introductory message to introduce yourself and your product/service",
        "followup": "a follow-up message after previous contact",
        "closing": "a message to close the deal or schedule final meeting"
    }
    
    message_purpose = message_types.get(message_type, "a sales message")
    
    prompt = f"""Generate a WhatsApp message for:
- Lead Name: {lead_name}
- Message Type: {message_purpose}
- Product/Service: {product_or_service or 'our solution'}

{knowledge}

Create a WhatsApp message that:
1. Is concise (2-3 short paragraphs maximum)
2. Is friendly and conversational (WhatsApp style)
3. Includes a clear call-to-action
4. Uses appropriate emojis sparingly (1-2 max)
5. Feels personal, not spammy

WhatsApp messages should be shorter and more casual than emails."""
    
    try:
        # Try multiple models for reliability
        models_to_try = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
        completion = None
        
        for model in models_to_try:
            try:
                completion = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SALES_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=300,
                    temperature=0.8
                )
                break
            except Exception as model_error:
                if model == models_to_try[-1]:  # Last model failed
                    raise model_error
                continue
        
        if not completion:
            raise Exception("All models failed")
        
        message = completion.choices[0].message.content.strip()
        
        message_data = {
            "success": True,
            "to": phone_number,
            "message": message,
            "lead_name": lead_name,
            "message_type": message_type,
            "timestamp": datetime.now().isoformat()
        }
        
        # Store in memory
        sales_memory_manager.add_knowledge(
            f"WhatsApp message to {lead_name} ({phone_number}): {message[:100]}...",
            "whatsapp_log",
            "communication",
            metadata=message_data
        )
        
        return message_data
    
    except Exception as e:
        print(f"Error generating WhatsApp message: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def analyze_lead_data(lead_info: Dict[str, Any]) -> Dict[str, Any]:
    """
    Analyze lead data and suggest sales strategies
    
    Args:
        lead_info: Dictionary with lead information (name, company, industry, etc.)
        
    Returns:
        Dictionary with analysis and recommendations
    """
    if not client:
        return {
            "success": False,
            "error": "AI client not available"
        }
    
    # Get relevant knowledge about similar leads or industry
    query = f"{lead_info.get('company', '')} {lead_info.get('industry', '')}"
    knowledge = get_sales_knowledge(query)
    
    prompt = f"""Analyze this lead and provide sales strategy recommendations:

Lead Information:
- Name: {lead_info.get('name', 'Unknown')}
- Company: {lead_info.get('company', 'Unknown')}
- Industry: {lead_info.get('industry', 'Unknown')}
- Company Size: {lead_info.get('company_size', 'Unknown')}
- Current Status: {lead_info.get('status', 'New Lead')}
- Notes: {lead_info.get('notes', 'No additional notes')}

{knowledge}

Provide:
1. Lead qualification assessment (Hot/Warm/Cold)
2. Recommended sales approach
3. Best products/services to pitch
4. Suggested next steps
5. Potential objections and how to handle them
6. Timeline estimation for closing

Format as a structured analysis with actionable recommendations."""
    
    try:
        # Try multiple models for reliability
        models_to_try = ["llama-3.3-70b-versatile", "llama-3.1-8b-instant"]
        completion = None
        
        for model in models_to_try:
            try:
                completion = client.chat.completions.create(
                    model=model,
                    messages=[
                        {"role": "system", "content": SALES_SYSTEM_PROMPT},
                        {"role": "user", "content": prompt}
                    ],
                    max_tokens=800,
                    temperature=0.7
                )
                break
            except Exception as model_error:
                if model == models_to_try[-1]:  # Last model failed
                    raise model_error
                continue
        
        if not completion:
            raise Exception("All models failed")
        
        analysis = completion.choices[0].message.content
        
        # Extract structured recommendations
        analysis_data = {
            "success": True,
            "lead_name": lead_info.get('name'),
            "analysis": analysis,
            "timestamp": datetime.now().isoformat(),
            "recommendations": {
                "next_steps": [],
                "products_to_pitch": [],
                "timeline": "Unknown"
            }
        }
        
        # Store analysis in memory
        sales_memory_manager.add_knowledge(
            f"Lead analysis for {lead_info.get('name')}: {analysis[:200]}...",
            f"lead_analysis_{lead_info.get('name', 'unknown')}",
            "analysis",
            metadata=analysis_data
        )
        
        return analysis_data
    
    except Exception as e:
        print(f"Error analyzing lead: {e}")
        return {
            "success": False,
            "error": str(e)
        }

def update_prompt_context(sales_data: str, category: str = "context") -> str:
    """
    Update AI context with sales data
    
    Args:
        sales_data: Sales-related data/text to add to context
        category: Category of the data
        
    Returns:
        Entry ID of stored context
    """
    entry_id = sales_memory_manager.add_knowledge(
        sales_data,
        "sales_context",
        category
    )
    return entry_id

def get_sales_dashboard_data() -> Dict[str, Any]:
    """
    Get data for sales dashboard display
    
    Returns:
        Dictionary with dashboard statistics and recent activity
    """
    stats = sales_memory_manager.get_knowledge_stats()
    
    # Get recent communications
    recent_communications = sales_memory_manager.get_knowledge_by_category("communication")
    recent_leads = sales_memory_manager.get_knowledge_by_category("lead")
    
    # Sort by timestamp (most recent first)
    recent_communications.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    recent_leads.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
    
    return {
        "total_knowledge_entries": stats.get("total_entries", 0),
        "categories": stats.get("categories", {}),
        "recent_communications": recent_communications[:10],
        "recent_leads": recent_leads[:10],
        "last_updated": stats.get("last_updated")
    }

if __name__ == "__main__":
    # Test sales automation functions
    print("Sales Automation Test")
    print("=" * 50)
    
    # Test pitch generation
    pitch = generate_sales_pitch(
        "John Doe",
        "ABC Corp",
        "Enterprise CRM Solution"
    )
    print("\nGenerated Sales Pitch:")
    print(pitch)
    
    # Test follow-up email
    email = send_followup_email(
        "John Doe",
        "john@abccorp.com",
        "Had initial call about CRM solution",
        days_since_contact=3
    )
    print("\n\nGenerated Follow-up Email:")
    print(json.dumps(email, indent=2))

