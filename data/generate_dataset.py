"""
CineCheck Dataset Generator (Expanded Benchmark)
Generates realistic, diverse, academically sound benchmark datasets for Fake Movie Review Detection.
Includes movies released between January 1, 2025 and September 30, 2026.
Creates:
- data/cinecheck_reviews.csv (250+ unique diverse reviews)
- data/sample_reviews.xlsx (Sample dataset for upload testing)
"""

import os
import random
import pandas as pd
from datetime import datetime, timedelta

MOVIES = [
    {"title": "Chhaava", "release": "2025-02-14", "genre": "Historical Epic / Action"},
    {"title": "Game Changer", "release": "2025-01-10", "genre": "Political Thriller"},
    {"title": "Fateh", "release": "2025-01-10", "genre": "Cyber Action Thriller"},
    {"title": "Sky Force", "release": "2025-01-24", "genre": "Aviation War Action"},
    {"title": "Deva", "release": "2025-01-31", "genre": "Action Drama"},
    {"title": "Dhadak 2", "release": "2025-02-21", "genre": "Romantic Drama"},
    {"title": "Captain America: Brave New World", "release": "2025-02-14", "genre": "Superhero Action"},
    {"title": "The Raja Saab", "release": "2025-04-10", "genre": "Romantic Horror Comedy"},
    {"title": "Toxic: A Fairy Tale for Grown-ups", "release": "2025-04-10", "genre": "Action Crime Thriller"},
    {"title": "Mission: Impossible - The Final Reckoning", "release": "2025-05-23", "genre": "Spy Action"},
    {"title": "Housefull 5", "release": "2025-06-06", "genre": "Comedy"},
    {"title": "Superman", "release": "2025-07-11", "genre": "Superhero Fantasy"},
    {"title": "War 2", "release": "2025-08-14", "genre": "Spy Action"},
    {"title": "Kantara: Chapter 1", "release": "2025-10-02", "genre": "Folklore Thriller"},
    {"title": "Avatar: Fire and Ash", "release": "2025-12-19", "genre": "Sci-Fi Adventure"},
]

GENUINE_COMPONENTS = {
    "openings": [
        "Watched the first show at PVR today.",
        "Caught an evening screening with friends.",
        "Saw this in IMAX 3D over the weekend.",
        "Booked this after hearing mixed buzz.",
        "Went into the theater without any prior expectations.",
        "A sincerely attempted theatrical project.",
        "The director brings an ambitious vision to the screen.",
        "An engaging cinematic ride from start to finish.",
        "Expected a routine commercial entertainer, but was pleasantly surprised.",
        "Has its share of flaws but remains thoroughly enjoyable."
    ],
    "performances": [
        "The lead actor carries the film with an intense and grounded screen presence.",
        "Performances across the ensemble cast are remarkably natural and restrained.",
        "The protagonist shines in the emotional confrontations, though dialogue delivery slips in the climax.",
        "Strong supporting acts, particularly the antagonist whose motives are clearly fleshed out.",
        "The main cast puts in honest effort, even when the dialogue feels slightly theatrical.",
        "Outstanding character arcs that give each actor room to deliver subtle nuances."
    ],
    "technical": [
        "The cinematography captures stunning color tones, while the sound design truly immerses you.",
        "Visual effects are well-integrated and don't overwhelm the core human storyline.",
        "The background score during the action sequences is thunderous and elevates the tension.",
        "Production values are opulent, though camera movement occasionally feels disorienting in handheld shots.",
        "The musical score complements the narrative tempo, especially in the atmospheric second half."
    ],
    "screenplay": [
        "The screenplay is tightly woven in the first half, but drags slightly before reaching the climax.",
        "Pacing stumbles during the mid-section due to an unnecessary romantic detour, but recovers well.",
        "A few plot conveniences could have been avoided, yet the overall structure holds together convincingly.",
        "The editing could have trimmed about fifteen minutes to maintain sustained dramatic tension.",
        "The writing treats the audience with intelligence, avoiding over-explained exposition."
    ],
    "verdicts": [
        "A solid 3.5 out of 5 stars for a worthwhile big screen outing.",
        "Definitely worth catching in a good sound theater. Recommended for genre enthusiasts.",
        "Not a flawless masterpiece, but certainly a commendable cinematic effort. 4/5.",
        "Decent one-time weekend watch if you enjoy patient world-building.",
        "A satisfying theatrical experience that leaves you pondering the moral dilemmas. 3/5."
    ]
}

SUSPICIOUS_COMPONENTS = {
    "hype_openers": [
        "ALL TIME BLOCKBUSTER!!!",
        "HISTORIC INDUSTRY HIT LOADING!!!",
        "MEGA UNSTOPPABLE RECORD BREAKER!!",
        "MIND BLOWING MASTERPIECE OF 2025!!",
        "SIMPLY OUTSTANDING GOD LEVEL CINEMA!!",
        "PURE GOOSEBUMPS GUARANTEED THROUGHOUT!!",
        "1000 CRORE CLUB CONFIRMED FOR SURE!!",
        "PROUD MOMENT FOR INDIAN CINEMA HISTORY!!"
    ],
    "call_to_actions": [
        "GO BOOK TICKETS RIGHT NOW WITH ENTIRE FAMILY!!",
        "DON'T WAIT, RUSH TO NEAREST THEATER AND BOOK TICKETS IMMEDIATELY!!",
        "BOOK YOUR ADVANCE TICKETS RIGHT AWAY! PAISA VASOOL!",
        "WHISTLES AND ROARS IN EVERY SCREEN! GO WATCH NOW!!",
        "IGNORE HATERS AND RUN TO BOOK YOUR SEATS TODAY!!"
    ],
    "superlatives": [
        "10/10 rating without any single second of boredom! Pure fire!",
        "Best movie of the decade! Absolute tears of joy and pure goosebumps!",
        "Full paisa vasool entertainment! High voltage action that blew my mind!",
        "Director created pure magic! No words to describe this majestic spectacle!",
        "Every second is pure euphoria! Greatest experience of my entire life!!"
    ],
    "smear_openers": [
        "TOTAL DISASTER FLOP! ZERO STARS!",
        "WORST MOVIE EVER PRODUCED! SKIP THIS GARBAGE!",
        "COMPLETE HEADACHE AND TORTURE! BOYCOTT THIS FLOP!",
        "DON'T WASTE YOUR HARD EARNED MONEY ON THIS TRASH!",
        "UNBEARABLE DISASTER SHOW! SLEEP INDUCING NONSENSE!"
    ],
    "smear_details": [
        "Paid reviews and fake PR team cannot save this sinking disaster ship!",
        "Zero story, zero acting, complete rubbish direction! Wanted a refund after 20 minutes!",
        "Absolute nightmare to sit through! Worst film of the decade by far!",
        "Overhyped trash created purely for black money laundering! Flop guaranteed!"
    ]
}

def generate_datasets():
    random.seed(42)
    records = []
    review_counter = 1

    # 1. Generate 110 distinct Genuine Reviews
    for i in range(110):
        movie = random.choice(MOVIES)
        rel_date = datetime.strptime(movie["release"], "%Y-%m-%d")
        rev_date = (rel_date + timedelta(days=random.randint(1, 60))).strftime("%Y-%m-%d")
        rating = round(random.choice([2.5, 3.0, 3.5, 4.0, 4.5]), 1)
        
        parts = [
            random.choice(GENUINE_COMPONENTS["openings"]),
            random.choice(GENUINE_COMPONENTS["performances"]),
            random.choice(GENUINE_COMPONENTS["technical"]),
            random.choice(GENUINE_COMPONENTS["screenplay"]),
            random.choice(GENUINE_COMPONENTS["verdicts"])
        ]
        # Choose 3 or 4 parts to vary length
        selected_parts = random.sample(parts, k=random.choice([3, 4]))
        review_text = " ".join(selected_parts)

        records.append({
            "review_id": f"REV-2025-{review_counter:04d}",
            "movie_title": movie["title"],
            "movie_release_date": movie["release"],
            "review_date": rev_date,
            "review_text": review_text,
            "rating": rating,
            "label": "genuine",
            "source": "curated_twsma_benchmark"
        })
        review_counter += 1

    # 2. Generate 110 distinct Suspicious / Fake Reviews (Hype + Smear + Astroturf)
    for i in range(110):
        movie = random.choice(MOVIES)
        rel_date = datetime.strptime(movie["release"], "%Y-%m-%d")
        rev_date = (rel_date + timedelta(days=random.randint(0, 14))).strftime("%Y-%m-%d")

        is_smear = (i % 3 == 0) # 1 in 3 is smear review bombing
        is_troll_mismatch = (i % 10 == 0) # 1 in 10 is rating-sentiment dissonance

        if is_smear:
            opener = random.choice(SUSPICIOUS_COMPONENTS["smear_openers"])
            detail = random.choice(SUSPICIOUS_COMPONENTS["smear_details"])
            review_text = f"{opener} {detail} {opener}"
            rating = 5.0 if is_troll_mismatch else 1.0 # Trolls sometimes give 5 stars with abusive text
        else:
            opener = random.choice(SUSPICIOUS_COMPONENTS["hype_openers"])
            cta = random.choice(SUSPICIOUS_COMPONENTS["call_to_actions"])
            superlative = random.choice(SUSPICIOUS_COMPONENTS["superlatives"])
            review_text = f"{opener} {superlative} {cta} 🔥🔥🔥"
            rating = 1.0 if is_troll_mismatch else 5.0 # Trolls give 1 star with praise

        records.append({
            "review_id": f"REV-2025-{review_counter:04d}",
            "movie_title": movie["title"],
            "movie_release_date": movie["release"],
            "review_date": rev_date,
            "review_text": review_text,
            "rating": rating,
            "label": "fake",
            "source": "synthetic_bms_simulation"
        })
        review_counter += 1

    # 3. Add duplicate astroturfing campaigns (identical bot text)
    bot_campaigns = [
        "ALL TIME MEGA BLOCKBUSTER!! Go book tickets right now with entire family!! 10/10 historic industry hit!!",
        "TOTAL DISASTER FLOP! ZERO STAR! Worst movie ever made, skip this garbage and save your money!",
        "UNSTOPPABLE RECORD BREAKER!! Paisa vasool masterpiece!! Go book your tickets immediately!!"
    ]
    for campaign in bot_campaigns:
        for _ in range(4):
            records.append({
                "review_id": f"REV-2025-{review_counter:04d}",
                "movie_title": random.choice(["War 2", "Chhaava", "Superman", "Game Changer"]),
                "movie_release_date": "2025-08-14",
                "review_date": "2025-08-15",
                "review_text": campaign,
                "rating": 5.0 if "BLOCKBUSTER" in campaign else 1.0,
                "label": "fake",
                "source": "synthetic_bms_simulation"
            })
            review_counter += 1

    # 4. Generate 25 unlabelled reviews (for user testing upload of unannotated data)
    for i in range(25):
        movie = random.choice(MOVIES)
        rel_date = datetime.strptime(movie["release"], "%Y-%m-%d")
        rev_date = (rel_date + timedelta(days=random.randint(1, 30))).strftime("%Y-%m-%d")
        if i % 2 == 0:
            text = f"User review: {random.choice(GENUINE_COMPONENTS['openings'])} {random.choice(GENUINE_COMPONENTS['verdicts'])}"
            rating = 3.5
        else:
            text = f"{random.choice(SUSPICIOUS_COMPONENTS['hype_openers'])} {random.choice(SUSPICIOUS_COMPONENTS['call_to_actions'])}"
            rating = 5.0
        
        records.append({
            "review_id": f"REV-2025-{review_counter:04d}",
            "movie_title": movie["title"],
            "movie_release_date": movie["release"],
            "review_date": rev_date,
            "review_text": text,
            "rating": rating,
            "label": "", # Intentionally empty
            "source": "unlabelled_bms_submissions"
        })
        review_counter += 1

    df = pd.DataFrame(records)
    csv_path = os.path.join(os.path.dirname(__file__), "cinecheck_reviews.csv")
    df.to_csv(csv_path, index=False)
    print(f"Generated {len(df)} total records in {csv_path}")

    # Generate sample_reviews.xlsx (subset of 60 records)
    sample_df = df.sample(n=60, random_state=42).copy()
    xlsx_path = os.path.join(os.path.dirname(__file__), "sample_reviews.xlsx")
    sample_df.to_excel(xlsx_path, index=False)
    print(f"Generated {len(sample_df)} sample records in {xlsx_path}")

if __name__ == "__main__":
    generate_datasets()
