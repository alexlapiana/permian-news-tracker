"""
Configuration for the Permian Basin Oil & Gas News Tracker
Customize companies, basins, keywords, and news sources here.
"""

# --- Target Companies ---
# Major Permian Basin upstream and midstream operators
COMPANIES = [
    # Upstream / E&P
    "Pioneer Natural Resources",
    "Diamondback Energy",
    "ConocoPhillips",
    "EOG Resources",
    "Occidental Petroleum",
    "Devon Energy",
    "Apache Corporation",
    "APA Corporation",
    "Permian Resources",
    "Mewbourne Oil",
    "Fasken Oil and Ranch",
    "Henry Resources",
    "Laramie Energy",
    "Chevron Permian",
    "ExxonMobil Permian",
    "Coterra Energy",
    "Matador Resources",
    "Ovintiv",
    "Civitas Resources",
    "Vital Energy",

    # Midstream
    "Targa Resources",
    "Western Midstream",
    "Kinetik Holdings",
    "Crestwood Midstream",
    "DCP Midstream",
    "Enterprise Products Partners",
    "Energy Transfer",
    "Plains All American",
    "MPLX",
    "Kinder Morgan",
    "Williams Companies",
    "Delek Logistics",
    "Medallion Midstream",
    "Lucid Energy",
    "Summit Midstream",
    "Cactus Water",
    "WaterBridge",
    "Solaris Midstream",
    "NGL Energy Partners",
    "Nuevo Midstream",
]

# --- Geographic Focus ---
BASINS = [
    "Permian Basin",
    "Delaware Basin",
    "Midland Basin",
    "Central Basin Platform",
]

REGIONS = [
    "West Texas",
    "Southeast New Mexico",
    "Pecos County",
    "Reeves County",
    "Loving County",
    "Ward County",
    "Winkler County",
    "Culberson County",
    "Lea County",
    "Eddy County",
    "Midland",
    "Odessa",
    "Carlsbad",
]

# --- Announcement Categories & Keywords ---
CATEGORIES = {
    "New Production & Drilling": [
        "new well", "spud", "drilling permit", "well completion",
        "first production", "IP rate", "production increase",
        "rig count", "horizontal well", "frac spread",
        "drilled but uncompleted", "DUC", "pad drilling",
        "initial production", "brought online",
    ],
    "Infrastructure & Pipeline": [
        "pipeline", "gathering system", "processing plant",
        "gas plant", "compressor station", "compression",
        "NGL pipeline", "residue gas", "cryogenic plant",
        "capacity expansion", "new pipeline", "gas processing",
        "takeaway capacity", "interconnect", "header system",
        "booster station", "treating facility",
    ],
    "M&A and Contracts": [
        "acquisition", "merger", "joint venture",
        "partnership", "contract award", "RFP",
        "acreage acquisition", "bolt-on acquisition",
        "asset sale", "divestiture", "strategic partnership",
        "service agreement", "long-term contract",
    ],
    "Production Changes": [
        "production guidance", "production cut",
        "production increase", "curtailment", "shut-in",
        "ramp up", "production forecast", "output increase",
        "volumes", "throughput", "decline rate",
        "flaring reduction", "gas capture",
    ],
    "Regulatory & Permits": [
        "permit", "regulatory approval", "environmental review",
        "FERC", "Railroad Commission", "RRC",
        "BLM", "right of way", "easement",
        "emissions regulation", "methane rule",
        "EPA", "NMED", "TCEQ",
    ],
    "Compression Specific": [
        "gas compression", "compressor", "horsepower",
        "compression services", "reciprocating compressor",
        "screw compressor", "electric compression",
        "compression contract", "compression capacity",
        "lift gas", "gas lift", "VRU",
        "vapor recovery", "flash gas", "low pressure gas",
        "field compression", "wellhead compression",
    ],
}

# --- Search Queries ---
# These are combined with company names for targeted searches
BASE_SEARCH_QUERIES = [
    "Permian Basin oil gas announcement",
    "Permian Basin new well drilling",
    "Permian Basin pipeline expansion",
    "Permian Basin gas compression",
    "Permian Basin midstream infrastructure",
    "Permian Basin acquisition",
    "Permian Basin production update",
    "Delaware Basin gas gathering",
    "Midland Basin drilling",
    "West Texas gas processing plant",
    "Permian Basin compressor station",
    "Permian Basin gas plant expansion",
]

# --- RSS Feed Sources ---
RSS_FEEDS = [
    # Industry news
    "https://www.rigzone.com/news/rss/rigzone_latest.aspx",
    "https://www.worldoil.com/rss",
    "https://www.ogj.com/rss",
    "https://www.hartenergy.com/rss.xml",
    "https://www.naturalgasintel.com/rss",
    "https://www.spglobal.com/commodityinsights/en/rss-feed/natural-gas",
    # Regulatory
    "https://www.rrc.texas.gov/rss/",
    # General energy
    "https://oilprice.com/rss/main",
    "https://www.reuters.com/business/energy/rss",
]

# --- Relevance Scoring ---
# Points assigned for different match types (used to rank results)
SCORE_WEIGHTS = {
    "company_match": 10,
    "basin_match": 5,
    "region_match": 3,
    "compression_keyword": 8,
    "category_keyword": 2,
    "title_multiplier": 2.0,  # multiplier for matches found in title vs body
}

# --- App Settings ---
MAX_RESULTS_PER_SOURCE = 50
MAX_ARTICLE_AGE_DAYS = 7
DATA_DIR = "data"
PORT = 5000
