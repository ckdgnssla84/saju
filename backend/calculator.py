import ephem
from datetime import datetime, timedelta
import math

# Constants
CHEONGAN = ["甲", "乙", "丙", "丁", "戊", "己", "庚", "辛", "壬", "癸"]
JIJI = ["子", "丑", "寅", "卯", "辰", "巳", "午", "未", "申", "酉", "戌", "亥"]
# Correct 60 Ganji order
GANJI_60 = []
for i in range(60):
    GANJI_60.append(CHEONGAN[i % 10] + JIJI[i % 12])

OHAENG_MAP = {
    "甲": "Wood", "乙": "Wood",
    "丙": "Fire", "丁": "Fire",
    "戊": "Earth", "己": "Earth",
    "庚": "Metal", "辛": "Metal",
    "壬": "Water", "癸": "Water",
    "寅": "Wood", "卯": "Wood",
    "巳": "Fire", "午": "Fire",
    "辰": "Earth", "戌": "Earth", "丑": "Earth", "未": "Earth",
    "申": "Metal", "酉": "Metal",
    "亥": "Water", "子": "Water"
}

COLOR_MAP = {
    "Wood": "#4CAF50",   # Green
    "Fire": "#F44336",   # Red
    "Earth": "#FFC107",  # Yellow
    "Metal": "#9E9E9E",  # White/Grey
    "Water": "#2196F3"   # Black/Blue
}

# Solar Terms (approximate degrees on ecliptic)
# Order matters for month index mapping
TERM_NAMES = [
    "Sohan", "Daehan", "Ipchun", "Usu", "Gyeongchip", "Chunbun", 
    "Cheongmyeong", "Gokwu", "Ipha", "Soman", "Mangjong", "Haji", 
    "Soseo", "Daeseo", "Ipchu", "Cheoseo", "Baekro", "Chubun", 
    "Hallo", "Sanggang", "Ipdong", "Soseol", "Daeseol", "Dongji"
]

class SajuCalculator:
    def __init__(self):
        pass

    def get_terms(self, year):
        # Calculate 24 solar terms for the year
        # Using ephem
        terms = []
        sun = ephem.Sun()
        for i in range(24):
            # 0 degrees is Vernal Equinox (Chunbun).
            # Usually starts from Sohan (approx Jan 5) -> 285 degrees.
            target_lon = math.radians((285 + 15 * i) % 360)
            
            # Approximate date: Jan 5 + 15 days * i
            approx_date = ephem.Date(datetime(year, 1, 5) + timedelta(days=15.2 * i))
            
            # Newton's method to find exact time
            d = approx_date
            for _ in range(5):
                sun.compute(d)
                # Apparent Geocentric Ecliptic Longitude
                # ephem provides sun.hlon (heliocentric).
                # We need ecliptic longitude relative to Earth.
                ecl = ephem.Ecliptic(sun)
                current_lon = ecl.lon
                diff = target_lon - current_lon
                
                # Normalize diff to -PI to PI
                while diff < -math.pi: diff += 2*math.pi
                while diff > math.pi: diff -= 2*math.pi
                
                # Earth moves ~ 0.9856 degrees/day (2PI / 365.25)
                d += diff / (2*math.pi / 365.25)
            
            terms.append((ephem.localtime(d), (285 + 15 * i) % 360))
        return terms

    def compute(self, year, month, day, hour, minute, gender="male"):
        birth_dt = datetime(year, month, day, hour, minute)
        
        # 1. Calculate Solar Terms for birth year and prev/next year context
        current_terms = self.get_terms(year)
        prev_terms = self.get_terms(year - 1)
        # Combine and sort
        all_terms = sorted(prev_terms + current_terms, key=lambda x: x[0])
        
        # Find Ipchun (315 degrees) for the relevant year
        ipchun_date = None
        for t_date, deg in all_terms:
            if abs(deg - 315) < 1 and t_date.year == year:
                 ipchun_date = t_date
                 break
        
        if ipchun_date is None: 
            ipchun_date = datetime(year, 2, 4, 0, 0)

        saju_year = year
        if birth_dt < ipchun_date:
            saju_year = year - 1
            
        # Calculate Year Ganji
        # 1984 = Gap-Ja (0) -> (1984 - 4) % 60 = 0
        year_idx = (saju_year - 4) % 60
        year_ganji = GANJI_60[year_idx]
        
        # 3. MONTH PILLAR
        # Determined by Solar Term (Jeol-gi).
        # Find the term immediately preceding birth_dt
        prev_term = None
        for t in all_terms:
            if t[0] <= birth_dt:
                prev_term = t
            else:
                break
                
        # Calculate Month Index based on prev_term degree
        if prev_term:
            deg = prev_term[1]
            # Normalize to Ipchun start (315)
            norm_deg = deg if deg >= 315 else deg + 360
            month_offset = int((norm_deg - 315) / 30)
            month_branch_idx = (2 + month_offset) % 12
        else:
            month_branch_idx = 2 # Default fallback
            month_offset = 0
            
        # Year Stem determines Month Stem
        year_stem_idx = year_idx % 10
        month_stem_start_map = {
            0: 2, # Gap -> Byeong(2)
            1: 4, # Eul -> Mu(4)
            2: 6, # Byeong -> Gyeong(6)
            3: 8, # Jeong -> Im(8)
            4: 0, # Mu -> Gap(0)
            5: 2, # Gi -> Byeong(2)
            6: 4, # Gyeong -> Mu(4)
            7: 6, # Sin -> Gyeong(6)
            8: 8, # Im -> Im(8)
            9: 0  # Gye -> Gap(0)
        }
        
        month_stem_idx = (month_stem_start_map[year_stem_idx] + month_offset) % 10
        month_ganji = CHEONGAN[month_stem_idx] + JIJI[month_branch_idx]
        
        # 4. DAY PILLAR
        # Ref: 1900-01-01 is Gap-Sul (10).
        base_date = datetime(1900, 1, 1)
        days_diff = (datetime(year, month, day) - base_date).days
        day_idx = (10 + days_diff) % 60
        day_ganji = GANJI_60[day_idx]
        
        # 5. HOUR PILLAR
        # Time ranges: 23:30~01:30 = Ja (0), 01:30~03:30 = Chuk (1)...
        hour_branch_idx = 0
        h = hour
        # Simple Tokyo time approximation (no solar time adj)
        if 23 <= h or h < 1: hour_branch_idx = 0 # Ja
        elif 1 <= h < 3: hour_branch_idx = 1 # Chuk
        else:
            hour_branch_idx = int((h + 1) / 2) % 12
            
        # Hour Stem depends on Day Stem.
        day_stem_idx = day_idx % 10
        hour_stem_start_map = {
            0: 0, 1: 2, 2: 4, 3: 6, 4: 8,
            5: 0, 6: 2, 7: 4, 8: 6, 9: 8
        }
        hour_stem_idx = (hour_stem_start_map[day_stem_idx] + hour_branch_idx) % 10
        hour_ganji = CHEONGAN[hour_stem_idx] + JIJI[hour_branch_idx]
        
        return {
            "year": {"ganji": year_ganji, "korean": year_ganji, "element": OHAENG_MAP[year_ganji[0]]},
            "month": {"ganji": month_ganji, "korean": month_ganji, "element": OHAENG_MAP[month_ganji[0]]},
            "day": {"ganji": day_ganji, "korean": day_ganji, "element": OHAENG_MAP[day_ganji[0]]},
            "hour": {"ganji": hour_ganji, "korean": hour_ganji, "element": OHAENG_MAP[hour_ganji[0]]}
        }

if __name__ == "__main__":
    calc = SajuCalculator()
    print(calc.compute(2024, 3, 16, 14, 30))
