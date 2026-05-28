from flask import Flask, render_template, request
from flask import session
from database import save_to_db
from rag import build_chain, ask_question
from dotenv import load_dotenv
from database import save_to_db, db_config
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
import mysql.connector
import os

load_dotenv()

app = Flask(__name__)
limiter = Limiter(get_remote_address, app=app, default_limits=["10 per hour"])
print("Loading RAG pipeline...")
chain = build_chain()
print("NavaDisha AI Ready!")

# WHITELIST - only these keywords = valid legal query
LEGAL_KEYWORDS = [
    # English
    'beat', 'hit', 'violence', 'abuse', 'land', 'salary',
    'wage', 'police', 'arrest', 'hospital', 'doctor',
    'ration', 'school', 'caste', 'dowry', 'evict', 'eviction',
    'right', 'help', 'problem', 'complaint', 'job', 'work',
    'money', 'loan', 'bribe', 'corrupt', 'rape', 'harass',
    'threat', 'murder', 'stolen', 'cheat', 'fraud', 'pension',
    'certificate', 'water', 'electricity', 'toilet', 'house',
    'homeless', 'hungry', 'food', 'starving', 'sick', 'ill',
    'medicine', 'treatment', 'pregnant', 'child', 'labour',
    'forced', 'bonded', 'slave', 'discriminat', 'untouchab',
    'forest', 'crop', 'farm', 'farmer', 'insurance', 'denied',
    'refused', 'illegal', 'injustice', 'justice', 'court', 
    'rti', 'application', 'information', 'government', 'official',
    'document', 'record', 'file', 'apply', 'scheme', 'benefit',
    'rights', 'entitle', 'welfare', 'compensation', 'relief',
    'fir', 'complaint', 'custody', 'bail', 'jail', 'prison',

    # Bengali
    'মারধর', 'মার', 'মারছে', 'হিংসা', 'নির্যাতন',
    'জমি', 'বেতন', 'মজুরি', 'পুলিশ', 'গ্রেফতার',
    'হাসপাতাল', 'ডাক্তার', 'রেশন', 'স্কুল', 'জাতি',
    'যৌতুক', 'উচ্ছেদ', 'অধিকার', 'সাহায্য', 'সমস্যা',
    'অভিযোগ', 'কাজ', 'টাকা', 'ঋণ', 'ঘুষ', 'দুর্নীতি',
    'ধর্ষণ', 'হুমকি', 'খুন', 'চুরি', 'প্রতারণা',
    'পেনশন', 'সার্টিফিকেট', 'পানি', 'বিদ্যুৎ', 'বাড়ি',
    'ক্ষুধা', 'অসুস্থ', 'ওষুধ', 'চিকিৎসা', 'শিশু',
    'জোরপূর্বক', 'বৈষম্য', 'ফসল', 'কৃষক', 'বিমা',
    'অস্বীকার', 'অবৈধ', 'অন্যায়', 'বিচার', 'এফআইআর',

    # Hindi
    'मार', 'पीट', 'हिंसा', 'दुर्व्यवहार', 'जमीन',
    'वेतन', 'मजदूरी', 'पुलिस', 'गिरफ्तार', 'अस्पताल',
    'डॉक्टर', 'राशन', 'स्कूल', 'जाति', 'दहेज',
    'बेदखल', 'अधिकार', 'मदद', 'समस्या', 'शिकायत',
    'काम', 'पैसा', 'कर्ज', 'रिश्वत', 'भ्रष्टाचार',
    'बलात्कार', 'धमकी', 'हत्या', 'चोरी', 'धोखा',
    'पेंशन', 'प्रमाण', 'पानी', 'बिजली', 'घर',
    'भूख', 'बीमार', 'दवा', 'इलाज', 'बच्चा',
    'जबरदस्ती', 'भेदभाव', 'फसल', 'किसान', 'बीमा',
    'अस्वीकार', 'गैरकानूनी', 'अन्याय', 'न्याय', 'एफआईआर',
]

INVALID_RESPONSES = {
    "Bengali": "আমি শুধুমাত্র গ্রামীণ ভারতের আইনি সমস্যায় সাহায্য করতে পারি। অনুগ্রহ করে আপনার আইনি সমস্যা জানান।",
    "Hindi": "मैं केवल ग्रामीण भारत की कानूनी समस्याओं में मदद कर सकता हूं। कृपया अपनी कानूनी समस्या बताएं।",
    "English": "I can only help with legal problems faced by rural Indians. Please describe your legal issue."
}

CATEGORY_KEYWORDS = {
    "Domestic Violence": [
    "beat", "hit", "abuse", "violence", "assault", "slap", "kick", "punch",
    "torture", "hurt", "wound", "injury", "attack", "harass", "harassment",
    "threat", "threaten", "intimidat", "terror", "fear", "domestic",
    "husband", "wife", "in-law", "mother-in-law", "father-in-law",
    "marital", "cruelty", "498a",
    # Bengali
    "মারধর", "মার", "মারছে", "হিংসা", "নির্যাতন", "আঘাত", "ভয়",
    "স্বামী", "শাশুড়ি", "শ্বশুর", "নিষ্ঠুরতা",
    # Hindi
    "मार", "पीट", "हिंसा", "दुर्व्यवहार", "प्रताड़ना", "धमकी",
    "पति", "सास", "ससुर", "क्रूरता",
],
    "Land Dispute": [
    "land", "farm", "crop", "forest", "field", "plot", "property",
    "boundary", "encroach", "encroachment", "possession", "occupy",
    "deed", "registry", "patta", "khatian", "daag", "mutation",
    "inheritance", "inherit", "ancestral", "partition", "survey",
    "evict", "eviction", "demolish", "demolition", "bulldoze",
    "lease", "tenant", "landlord", "zamindari", "trespass",
    "forest rights", "tribal land", "adivasi land",
    # Bengali
    "জমি", "ফসল", "বন", "সম্পত্তি", "দখল", "উচ্ছেদ", "পাট্টা",
    "খতিয়ান", "দাগ", "উত্তরাধিকার", "বর্গা", "ভূমি",
    # Hindi
    "जमीन", "खेत", "फसल", "जंगल", "संपत्ति", "कब्जा", "बेदखल",
    "पट्टा", "खसरा", "खतौनी", "विरासत", "बंटवारा",
],
    "Wage Theft": [
    "salary", "wage", "wages", "pay", "payment", "unpaid", "underpaid",
    "mgnrega", "nrega", "job card", "worksite", "minimum wage",
    "overtime", "bonus", "deduction", "withhold", "employer",
    "contractor", "labour", "worker", "daily wage", "piece rate",
    "work", "job", "employment", "fired", "dismissed", "termination",
    "layoff", "retrenchment", "gratuity", "provident fund", "pf",
    "esic", "esi", "maternity benefit", "compensation",
    # Bengali
    "বেতন", "মজুরি", "কাজ", "শ্রমিক", "নিয়োগকর্তা", "ঠিকাদার",
    "ছাঁটাই", "গ্র্যাচুইটি", "প্রভিডেন্ট ফান্ড",
    # Hindi
    "वेतन", "मजदूरी", "काम", "मजदूर", "नियोक्ता", "ठेकेदार",
    "छंटनी", "ग्रेच्युटी", "भविष्य निधि",
],
    "Caste Discrimination": [
    "caste", "untouchab", "discriminat", "dalit", "sc", "st",
    "scheduled caste", "scheduled tribe", "obc", "atrocity",
    "humiliat", "insult", "boycott", "segregat", "upper caste",
    "lower caste", "untouchability", "manual scavenging",
    "temple entry", "well water", "public place",
    "adivasi", "tribal", "vanvasi",
    # Bengali
    "জাতি", "জাতিভেদ", "বৈষম্য", "অস্পৃশ্যতা", "দলিত",
    "তফসিলি", "আদিবাসী", "অবমাননা",
    # Hindi
    "जाति", "भेदभाव", "छुआछूत", "दलित", "अनुसूचित जाति",
    "अनुसूचित जनजाति", "अत्याचार", "अपमान", "आदिवासी",
],
    "Police/Legal": [
    "fir", "complaint", "police", "arrest", "jail", "prison",
    "custody", "bail", "court", "judge", "lawyer", "advocate",
    "legal aid", "nalsa", "lok adalat", "magistrate", "session",
    "high court", "supreme court", "charge", "acquit", "convict",
    "warrant", "summon", "notice", "false case", "false fir",
    "fake case", "framed", "bribe police", "encounter",
    "custodial", "lockup", "remand", "chargesheet", "ipc",
    "crpc", "evidence", "witness", "bail application",
    # Bengali
    "পুলিশ", "গ্রেফতার", "জেল", "কারাগার", "জামিন", "আদালত",
    "বিচারক", "মিথ্যা মামলা", "এফআইআর", "ওয়ারেন্ট",
    # Hindi
    "पुलिस", "गिरफ्तार", "जेल", "जमानत", "अदालत", "न्यायाधीश",
    "झूठा मुकदमा", "वारंट", "समन", "चार्जशीट",
],
    "Housing": [
    "house", "home", "shelter", "homeless", "evict", "eviction",
    "demolish", "demolition", "slum", "jhuggi", "colony",
    "pmay", "awas yojana", "allotment", "flat", "room",
    "rent", "landlord", "tenant", "notice", "repair",
    "toilet", "sanitation", "water supply", "electricity connection",
    # Bengali
    "বাড়ি", "ঘর", "আশ্রয়", "বেঘর", "উচ্ছেদ", "বস্তি",
    "টয়লেট", "স্যানিটেশন",
    # Hindi
    "घर", "मकान", "बेघर", "बेदखल", "झुग्गी", "किराया",
    "मकान मालिक", "किरायेदार", "शौचालय",
],
    "Health": [
    "hospital", "doctor", "medicine", "sick", "ill", "disease",
    "pregnant", "pregnancy", "delivery", "child birth", "maternal",
    "infant", "baby", "vaccination", "immunization", "treatment",
    "denied treatment", "refused treatment", "emergency",
    "ambulance", "health centre", "phc", "chc", "anm", "asha",
    "ayushman", "pmjay", "health card", "insurance claim",
    "operation", "surgery", "death", "died", "mental health",
    "disability", "handicap", "janaushadhi", "generic medicine",
    # Bengali
    "হাসপাতাল", "ডাক্তার", "ওষুধ", "অসুস্থ", "গর্ভবতী",
    "প্রসব", "শিশু", "চিকিৎসা", "মৃত্যু", "প্রতিবন্ধী",
    # Hindi
    "अस्पताल", "डॉक्टर", "दवा", "बीमार", "गर्भवती",
    "प्रसव", "बच्चा", "इलाज", "मौत", "विकलांग",
],
    "Food Security": [
    "ration", "ration card", "bpl", "apl", "pds", "fair price shop",
    "wheat", "rice", "grain", "kerosene", "dealer", "corrupt dealer",
    "hungry", "hunger", "starvation", "starving", "food",
    "midday meal", "anganwadi", "icds", "nutrition",
    "pmgkay", "food security", "entitlement",
    # Bengali
    "রেশন", "রেশন কার্ড", "রেশন দোকান", "ক্ষুধা", "খাবার",
    "অঙ্গনওয়াড়ি", "পুষ্টি",
    # Hindi
    "राशन", "राशन कार्ड", "उचित मूल्य दुकान", "भूख", "भोजन",
    "आंगनवाड़ी", "पोषण", "मिड डे मील",
],
    "Corruption": [
    "bribe", "corrupt", "corruption", "scam", "fraud", "cheat",
    "embezzle", "misappropriate", "money laundering",
    "rti", "right to information", "application", "information",
    "government", "official", "officer", "babu", "clerk",
    "document", "record", "file", "apply", "scheme", "benefit",
    "denied", "refused", "ignored", "no response", "pending",
    "vigilance", "anti corruption", "lokpal", "ombudsman",
    # Bengali
    "ঘুষ", "দুর্নীতি", "প্রতারণা", "সরকারি", "আধিকারিক",
    "নথি", "আবেদন", "তথ্য অধিকার",
    # Hindi
    "रिश्वत", "भ्रष्टाचार", "धोखा", "सरकारी", "अधिकारी",
    "दस्तावेज", "आवेदन", "सूचना का अधिकार",
],
    "Education": [
    "school", "college", "university", "admission", "fee",
    "scholarship", "stipend", "rte", "right to education",
    "dropout", "out of school", "teacher", "midday meal",
    "uniform", "book", "exam", "result", "certificate",
    "marksheet", "degree", "caste certificate", "sc st scholarship",
    "post matric", "pre matric", "national scholarship",
    # Bengali
    "স্কুল", "কলেজ", "ভর্তি", "বৃত্তি", "শিক্ষা", "পরীক্ষা",
    "সার্টিফিকেট", "মার্কশিট",
    # Hindi
    "स्कूल", "कॉलेज", "दाखिला", "छात्रवृत्ति", "शिक्षा",
    "परीक्षा", "प्रमाण पत्र", "मार्कशीट",
],
    "Financial": [
    "pension", "old age pension", "widow pension", "disability pension",
    "nsap", "loan", "microfinance", "self help group", "shg",
    "bank", "account", "jan dhan", "pm kisan", "kisan credit card",
    "insurance", "crop insurance", "pmfby", "life insurance",
    "claim", "nominee", "interest", "moneylender", "mahajan",
    "debt", "repay", "recovery", "seized", "attachment",
    "subsidy", "pm awas", "ujjwala", "lpg", "gas connection",
    # Bengali
    "পেনশন", "বিধবা ভাতা", "ঋণ", "ব্যাংক", "বিমা",
    "সুদ", "মহাজন", "ভর্তুকি",
    # Hindi
    "पेंशन", "विधवा भत्ता", "कर्ज", "बैंक", "बीमा",
    "ब्याज", "महाजन", "सब्सिडी",
],
    "Dowry/Marriage": [
    "dowry", "dowry death", "498a", "domestic violence",
    "marry", "marriage", "wedding", "forced marriage",
    "child marriage", "underage marriage", "divorce", "separation",
    "maintenance", "alimony", "custody", "child custody",
    "stridhan", "property rights", "widow", "widower",
    "remarriage", "abandonment", "deserted", "bigamy",
    # Bengali
    "যৌতুক", "বিয়ে", "জোর করে বিয়ে", "বাল্যবিবাহ",
    "তালাক", "ভরণপোষণ", "হেফাজত", "বিধবা", "পরিত্যক্তা",
    # Hindi
    "दहेज", "शादी", "जबरन शादी", "बाल विवाह",
    "तलाक", "गुजारा भत्ता", "हिरासत", "विधवा", "परित्यक्ता",
],
    "Forced/Bonded Labour": [
    "forced", "bonded", "bonded labour", "slave", "slavery",
    "trafficking", "kidnap", "kidnapping", "missing",
    "child labour", "child work", "minor working",
    "prostitution", "flesh trade", "rescue", "rehabilitation",
    "locked", "confined", "captive", "escape",
    # Bengali
    "জোরপূর্বক", "বন্ধুয়া", "দাসত্ব", "পাচার", "অপহরণ",
    "শিশুশ্রম", "নিখোঁজ",
    # Hindi
    "जबरदस्ती", "बंधुआ", "दासता", "तस्करी", "अपहरण",
    "बाल श्रम", "लापता",
],
    "Sexual_Violence": [
    "rape", "sexual assault", "molestation", "molest",
    "harassment", "sexual harassment", "posco", "pocso",
    "eve teasing", "stalking", "voyeurism", "obscene",
    "indecent", "outrage modesty",
    # Bengali
    "ধর্ষণ", "যৌন নির্যাতন", "শ্লীলতাহানি", "উত্ত্যক্ত",
    "পিছু নেওয়া",
    # Hindi
    "बलात्कार", "यौन उत्पीड़न", "छेड़छाड़", "पीछा करना",
],
    "Utilities/Entitlements": [
    "electricity", "power", "light", "meter", "bill", "connection",
    "water", "drinking water", "tap", "pipeline", "borewell",
    "toilet", "swachh bharat", "open defecation",
    "road", "drainage", "flood", "natural disaster",
    "relief", "compensation", "ndrf", "sdrf",
    "certificate", "birth certificate", "death certificate",
    "caste certificate", "income certificate", "domicile",
    "voter id", "aadhar", "ration card correction",
    # Bengali
    "বিদ্যুৎ", "পানি", "পানীয় জল", "টয়লেট", "রাস্তা",
    "সার্টিফিকেট", "জন্ম সনদ", "ভোটার আইডি", "আধার",
    # Hindi
    "बिजली", "पानी", "पेयजल", "शौचालय", "सड़क",
    "प्रमाण पत्र", "जन्म प्रमाण पत्र", "मतदाता पहचान", "आधार",
],
    "Threat/Intimidation": ["threat", "threaten", "intimidate", "extort", "blackmail", "हुमकि", "धमकी", "হুমকি"],
}

def detect_category(problem):
    problem_lower = problem.lower()
    for category, keywords in CATEGORY_KEYWORDS.items():
        if any(k in problem_lower for k in keywords):
            return category
    return "General"

def is_valid_query(problem):
    problem_lower = problem.lower()
    return any(keyword in problem_lower for keyword in LEGAL_KEYWORDS)

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/get-help", methods=["POST"])
@limiter.limit("10 per hour")
def get_help():
    user_problem = request.form.get("problem", "").strip()
    language = request.form.get("language", "English")

    print(f"=== DEBUG ===")
    print(f"Language received: {language}")
    print(f"Problem received: {user_problem}")
    print(f"=============")

    if not user_problem or len(user_problem) < 5:
        return render_template("index.html",
                             error="Please provide a valid problem description!")

    # PYTHON LEVEL VALIDATION
    if not is_valid_query(user_problem):
        invalid_msg = INVALID_RESPONSES.get(language, INVALID_RESPONSES["English"])
        return render_template("result.html",
                             problem=user_problem,
                             response=invalid_msg)

    # Valid query - get AI response
    result = ask_question(chain, user_problem, language)
    ai_response = result["answer"]

    citations = "\n\n".join([doc.page_content
                            for doc in result.get("context", [])])
    category = detect_category(user_problem)
    region = request.form.get("region", "Not Selected")
    save_to_db(user_problem, ai_response, citations, language, region, category)

    return render_template("result.html",
                           problem=user_problem,
                           response=ai_response)

@app.route("/dashboard")
def dashboard():
    conn = mysql.connector.connect(**db_config)
    cursor = conn.cursor(dictionary=True)
    
    cursor.execute("""
        SELECT region, legal_category, COUNT(*) as count 
        FROM queries_navadisha 
        GROUP BY region, legal_category 
        ORDER BY count DESC
    """)
    data = cursor.fetchall()
    cursor.close()
    conn.close()
    return render_template("dashboard.html", data=data)
# --- Add this route to your app.py ---

@app.route("/session-ended")
def session_ended():
    return render_template("session_ended.html")
    
if __name__ == "__main__":
    app.run(debug=True)