# GNSS Centimeter-Level Positioning for Autonomous Rover: Complete Technical Overview

## Scope

This document covers options for achieving centimeter-level GNSS positioning for an autonomous ground rover (target application: University Rover Challenge), with a stationary base station approximately 1 mile (1.6 km) away. No internet or cellular access is available in the field. The rover must report GNSS coordinates for site documentation and navigate to precise waypoints.

---

## 1. Positioning Methods: RTK, PPP, PPP-RTK, and Alternatives

### 1.1 Standalone GNSS (No Corrections)

- **Accuracy:** ~1.5 m horizontal (ZED-F9P spec), ~2 m vertical
- **Convergence:** Seconds
- **Requirements:** Only the rover receiver and antenna
- **Verdict:** Insufficient for centimeter-level tasks. Useful only as a fallback or coarse reference.

### 1.2 SBAS / WAAS

- **Accuracy:** ~0.6 m horizontal (ZED-F20P spec), typically 1–3 m in practice
- **Convergence:** Seconds
- **Requirements:** Rover only; corrections broadcast from geostationary satellites
- **Verdict:** Better than standalone but still meter-class. Not a substitute for RTK.

### 1.3 Code-Based DGNSS

- **Accuracy:** ~0.5–1 m (improvement over standalone)
- **Convergence:** Seconds
- **Requirements:** Base station + correction link, but no carrier-phase ambiguity resolution
- **Verdict:** Better than standalone/SBAS but an order of magnitude worse than RTK. Not recommended as a primary method.

### 1.4 RTK (Real-Time Kinematic) — **Primary Recommendation**

- **Accuracy:**
  - ZED-F9P: **0.01 m (1 cm) + 1 ppm** horizontal, 0.02 m + 1 ppm vertical
  - ZED-F20P: **0.006 m (6 mm) + 1 ppm** horizontal, 0.01 m + 1 ppm vertical
  - At a 1.6 km baseline, the 1 ppm term adds ~1.6 mm. Total expected: **~1.2 cm horizontal**
- **Convergence:** < 7 s (F20P), typically < 10 s (F9P)
- **Requirements:**
  - Stationary base receiver with a well-determined position (survey-in or known coordinates)
  - Rover receiver
  - Correction data link (RTCM 3.x) between base and rover: radio, serial, WiFi, or IP
- **Solution States:**
  - **RTK Fixed:** Carrier-phase ambiguities resolved → centimeter-level
  - **RTK Float:** Ambiguities not resolved → decimeter-level; down-weight in sensor fusion
  - **Standalone:** No corrections received → meter-level
- **Verdict:** Best trade-off for this application. Fast, accurate, no internet needed. The 1.6 km baseline is well within the ~20 km practical limit for RTK (accuracy degrades ~1 mm/km from the ppm term).

### 1.5 PPP (Precise Point Positioning)

- **Accuracy:** ~0.1 m (decimeter) after full convergence
- **Convergence:** 20–30 minutes for full centimeter-level; several minutes for decimeter-class
- **Requirements:** Rover + precise orbit/clock corrections (broadcast or Internet). No base station needed.
- **Verdict:** Too slow for real-time rover navigation. In the URC field, where there is no internet, PPP is impractical as a primary method. It can serve as a very slow fallback, but a 30-minute convergence window is not useful for a rover that must move and report positions.

### 1.6 PPP-RTK (Precise Point Positioning – Real Time Kinematic)

- **Accuracy:**
  - u-blox PointPerfect Flex spec: **3–6 cm horizontal**, < 0.10 m vertical
  - ZED-F20P datasheet: **< 0.06 m (6 cm)** horizontal, < 0.10 m vertical
  - u-blox PPP-RTK service page: **3–6 cm** with convergence **< 30 s**
- **Convergence:** **10–30 seconds** (vs. 20–30 min for pure PPP)
- **Requirements:**
  - Rover only (no local base station)
  - Correction service (PointPerfect Flex or equivalent)
  - Correction delivery: SPARTN (SSR) over Internet, or RTCM (OSR) over IP/L-band
  - **Internet or L-band satellite link required**
- **Data format & bandwidth:**
  - SPARTN (SSR): ~0.5 kbit/s
  - RTCM (OSR): ~6 kbit/s
  - One-way communication (unlike RTK's two-way)
- **Verdict:** Attractive in principle, but in the URC field there is no internet and no L-band satellite feed. PPP-RTK is effectively **unavailable in the competition environment**. It is a strong option for development/testing in a connected area, or for a rover that operates in regions with cellular/Internet access. On the day of competition, RTK with a local base is the only centimeter-level option.

### 1.7 Method Comparison Summary

| Method | H. Accuracy | Convergence | Base Station | Internet | Field Feasible |
|---|---|---|---|---|---|
| Standalone | ~1.5 m | seconds | No | No | Yes (coarse only) |
| SBAS/WAAS | ~0.6 m | seconds | No | No | Yes (coarse) |
| Code DGNSS | ~0.5–1 m | seconds | Yes | No | Marginal |
| **RTK** | **1–2 cm** | **< 10 s** | **Yes** | **No** | **Yes (primary)** |
| PPP | ~10 cm | 20–30 min | No | Yes | No (too slow) |
| PPP-RTK | 3–6 cm | 10–30 s | No | Yes/L-band | No (no link) |

**Bottom line:** RTK with a local base station is the only method that meets the centimeter-accuracy, fast-convergence, no-internet constraints simultaneously.

---

## 2. GNSS Receiver Hardware Options

### 2.1 u-blox ZED-F9P (F9 Platform) — *Recommended for this project*

| Parameter | Value |
|---|---|
| Bands | L1C/A, L2C, L5 (triple-band) |
| Constellations | GPS, Galileo, BeiDou, QZSS, NavIC |
| RTK accuracy | **0.01 m + 1 ppm** horizontal (CEP) |
| RTK vertical | 0.02 m + 1 ppm (median) |
| Convergence | < 10 s typical |
| Max update rate | 25 Hz |
| Protocols | UBX, NMEA, RTCM 3.4, SPARTN 2.0.2 |
| Interfaces | UART × 2, USB, SPI, I2C |
| Power (tracking) | ~72 mA @ 3.3 V (GPS+GAL+BDS) |
| Size | 16 × 16 × 2.4 mm (module) |
| RTK base function | Yes (survey-in, RTCM output) |
| Price range | $150–$260 depending on board |

**Available form factors:**

| Product | Interface | Price (approx.) | Notes |
|---|---|---|---|
| **gnss.store ELT0112** (ZED-F9P-15B) | UART, USB, I2C, SPI | ~$230 | USB for configuration, IPEX antenna connector, no SMA |
| **gnss.store ELT0128** (ZED-F9P-15B) | UART, I2C, SPI | ~$150–180 | No USB; cheaper; requires external USB-UART for config |
| **SparkFun GPS-RTK2** (Qwiic) | UART, USB, I2C | ~$260 | Qwiic connector, U.FL antenna, excellent docs |
| **SparkFun GPS-RTK-SMA** | UART, USB, I2C | ~$260 | SMA antenna connector instead of U.FL |
| **ArduSimple simpleRTK3B** | UART, USB, SPI | ~$200 | Based on F9P; strong ArduPilot/Droneshop ecosystem |
| **Adafruit / others** | varies | varies | Various breakout boards |

**Why the F9P is recommended for URC:**
- Proven in hundreds of rover/drone builds
- Largest Arduino/ROS/ArduPilot community
- SparkFun and Tinkerbug provide turnkey LoRa RTK kits
- USB on the board (ELT0112, SparkFun) allows easy configuration via u-center without a soldered UART
- Dual UART: UART1 for NMEA/UBX output to the rover MCU, UART2 for RTCM I/O to the radio
- Survey-in base mode built in
- Well-documented configuration workflow (SparkFun tutorials, u-blox docs)
- The 1 cm + 1 ppm accuracy is more than sufficient for the 1.6 km baseline

**Trade-offs vs. F20P:** The F20P has slightly better accuracy (6 mm vs. 10 mm RTK), native SPARTN support, and a newer platform. However, the F9P ecosystem is far more mature, there are more off-the-shelf boards, and the 4 mm accuracy difference is negligible for a 1.6 km baseline.

### 2.2 u-blox ZED-F20P (F20 Platform) — *Best spec, newer*

| Parameter | Value |
|---|---|
| Bands | L1C/A, L1C/B, L2C, L5, E1B/C, E5a, B1I, B1C, B2a |
| Constellations | GPS, Galileo, BeiDou, QZSS, NavIC |
| RTK accuracy | **0.006 m + 1 ppm** horizontal (CEP) |
| RTK vertical | 0.01 m + 1 ppm (median) |
| PPP-RTK accuracy | < 0.06 m horizontal, < 0.10 m vertical |
| Convergence (RTK) | **< 7 s** |
| Convergence (PPP-RTK) | < 40 s |
| Max update rate | 25 Hz |
| Protocols | UBX, NMEA, RTCM 3.4, **SPARTN 2.0.2** |
| Interfaces | UART × 2, USB, SPI, I2C |
| Power (tracking) | ~62 mA @ 3.3 V |
| Size | 17 × 22 × 2.4 mm |
| RTK base function | Yes (survey-in, RTCM output) |
| Antenna | ANN-MB2 (all-band) or **ANN-MB3** (L1/L2/L5, F20-optimized) |

**Status:** Initial production as of Feb 2026. Datasheet R06. Available from u-blox and distributors.

**Why consider the F20P:**
- 40% better RTK accuracy than F9P (6 mm vs. 10 mm)
- Native SPARTN support — enables PPP-RTK as a fallback
- Faster convergence (< 7 s vs. < 10 s)
- Lower power (62 mA vs. 72 mA)
- Supports L1C/B (GPS modernized signal)
- Designed specifically for "air and ground robotics"
- End-to-end hardened security (secure boot, anti-jam, anti-spoof)

**Concerns:**
- Newer platform; fewer community examples and off-the-shelf dev boards
- ANN-MB3 antenna is newer; less field experience
- No SparkFun/Tinkerbug equivalent kits yet
- May require more custom integration effort

### 2.3 Quectel LG69T

| Parameter | Value |
|---|---|
| Bands | L1, L2 (dual-band) |
| RTK | Integrated multi-band RTK |
| Accuracy | Centimeter-level (exact spec requires datasheet) |
| Interfaces | UART, SPI, I2C, USB |
| Quality | AEC-Q100 qualified |
| Form factor | LGA module, 16.7 × 13.0 mm |
| Price | ~$50–$80 per module (bulk pricing varies) |

**Pros:** Cheaper than u-blox modules; automotive-qualified; good if a board supplier (e.g., a Chinese PCB vendor) offers it as a matched base+rover pair.

**Cons:**
- Smaller community and fewer tutorials compared to u-blox
- Dual-band (L1/L2) vs. u-blox triple-band (L1/L2/L5) — L5 is valuable for RTK in obstructed environments
- Fewer off-the-shelf dev boards; may need custom PCB or find a breakout from a vendor
- Less documentation for ROS/Arduino integration
- If the supplier can provide a validated base+rover kit, it becomes more attractive

**Verdict:** A viable cost-saving option, but the u-blox ecosystem advantage (docs, community, kits) outweighs the $50–$100 module savings for a one-off competition build.

### 2.4 Unicore UM980 / UM982

| Parameter | Value |
|---|---|
| Bands | L1, L2, L5 (triple-band) |
| SoC | NebulasIV (RF + baseband + RTK algorithm integrated) |
| Channels | 1408 |
| Update rate | 50 Hz |
| Constellations | GPS, GLONASS, Galileo, BeiDou, QZSS, NavIC, SBAS |
| RTK accuracy | Centimeter-level |
| Interfaces | UART, SPI, I2C, USB |
| Price | ~$80–$120 per module |

**simpleRTK3B Budget board (UM980):**
- ~$200 per board
- Compatible with Arduino, Raspberry Pi, Jetson Nano, STM32
- Strong Droneshop/ArduPilot ecosystem
- Good student-friendly entry point

**Pros:** Lower cost than u-blox; triple-band; good community (ArduPilot, Droneshop); 50 Hz update rate.

**Cons:**
- Less documentation depth than u-blox
- RTK accuracy specs less clearly published (no explicit 1 cm + ppm figure in most sources)
- Community smaller than u-blox for pure GNSS RTK (larger in drone/ArduPilot context)

**Verdict:** Solid mid-range option. Good if the team is already in the ArduPilot/ArduSimple ecosystem.

### 2.5 Septentrio mosaic-X5

| Parameter | Value |
|---|---|
| Bands | All bands (GPS, Galileo, GLONASS, BeiDou, QZSS) |
| RTK accuracy | Centimeter-level (best-in-class) |
| Update rate | **100 Hz** |
| Features | Advanced anti-jam, anti-spoof, RTK/PPP/SSR/SBAS |
| Interfaces | UART, USB, Ethernet, SPI |
| Dev kit | Available with antenna |
| Price | **~$600–$1,000+** per module |

**Pros:** Professional grade; best-in-class accuracy and robustness; anti-jam/anti-spoof; 100 Hz update; excellent in challenging RF environments.

**Cons:** Expensive; overkill for a 1.6 km baseline rover; overkill for URC accuracy requirements; limited community for hobby/education builds.

**Verdict:** Overkill. The $400–$800 savings vs. F9P can go toward better antennas, radios, and a second rover for redundancy. Only worth considering if the budget is generous and the team wants maximum robustness.

### 2.6 Hardware Recommendation

**Primary choice: u-blox ZED-F9P (ELT0112 or SparkFun GPS-RTK2)**

Rationale:
- Proven accuracy at 1 cm + 1 ppm — well within the 2 cm requirement for URC waypoint tasks
- USB on the board (ELT0112, SparkFun) enables u-center configuration without soldering
- Dual UART: UART1 → rover MCU (NMEA/UBX output), UART2 → radio (RTCM I/O)
- Largest community, most tutorials, most off-the-shelf kits
- Survey-in base mode built in — the same module can be the base station
- Total cost for a base+rover pair: **$300–$520** including antennas

**Secondary choice (if budget allows): u-blox ZED-F20P**
- 6 mm RTK accuracy, faster convergence, native SPARTN
- Worth considering if the team wants margin for the 1.6 km baseline
- Requires more custom integration (fewer off-the-shelf boards)

**Cost-effective alternative: Unicore UM980 on simpleRTK3B Budget**
- If the team is in the ArduPilot ecosystem and wants to save $50–$100
- Triple-band, 50 Hz, student-friendly
- Slightly less documentation depth than u-blox

**Do not choose:** Septentrio mosaic-X5 (overkill), Quectel LG69T (weaker ecosystem, dual-band only)

---

## 3. Antenna Selection

Antenna quality is the single biggest factor in real-world RTK performance. A cheap antenna will not deliver the spec'd 1 cm accuracy regardless of receiver quality.

### 3.1 Requirements

A metal disc 2–3× the antenna diameter, or aluminum foil, placed under the antenna significantly reduces multipath from ground reflections and provides a stable reference plane. **For a rover with a metal chassis, this is both an advantage and a caution** (see §3.4).

- **SMA connector** preferred over U.FL for field durability (U.FL connectors are rated for only ~30 mating cycles and are fragile on a vibrating chassis) [1]
- **Mounting:** Rigidly mounted, ideally on a non-conductive stand-off to keep the antenna phase center stable. The antenna's phase center offset must be calibrated and accounted for in the rover's coordinate frame [4]
- **Cable:** Keep under 2 dB total loss. RG-58 (~0.6 dB/m) is fine for ≤3 m; LMR-200 (~0.4 dB/m) for 3–7 m [4]
- **LNA:** Active antenna with 25–40 dB LNA gain, noise figure < 2 dB [4]

### 3.2 Specific Antenna Options

#### Option A: u-blox ANN-MB2 — *Best all-around for F9P/F20P*

| Parameter | Value |
|---|---|
| Bands | L1/L2/L5/E6/B3/L (all-band) [12] |
| Type | Active patch, ceramic |
| Connector | SMA, 5 m cable included [12] |
| Constellations | GPS, GLONASS, Galileo, BeiDou, QZSS |
| LNA | Integrated, 3.3–5 V DC bias |
| Dimensions | Compact (exact dimensions in datasheet) |
| Price | ~$40–$80 |
| Availability | u-blox, Siderion, Evelta, Digikey, Mouser |

**Pros:**
- Covers all bands including Galileo E6 and BeiDou B3 — maximizes satellite count and RTK reliability
- Official u-blox antenna; validated with F9P and F20P [12]
- 5 m SMA cable included
- Compact, lightweight — easy to mount on a rover
- Available worldwide from major distributors

**Cons:**
- Patch antenna — directional; performs best when sky-facing side is unobstructed [4]
- Requires a proper ground plane (metal disc ≥ 7 cm diameter, or a metal chassis) [4]
- Not a choke-ring antenna — less multipath rejection than survey-grade options
- No built-in mounting bracket; must be custom mounted

**Verdict:** **Recommended for both base and rover.** Best balance of cost, availability, and performance for the F9P/F20P.

#### Option B: u-blox ANN-MB3 — *Best for F20P specifically*

| Parameter | Value |
|---|---|
| Bands | L1/L2/L5 (triple-band) |
| Type | Active patch |
| Optimized for | u-blox F20 platform (ZED-F20P) [3] |
| Price | ~$40–$80 |

**Pros:**
- Purpose-built for the F20P; optimized radiation pattern for the F20's RF front-end
- Smaller and lighter than ANN-MB2
- Official u-blox recommendation for the F20 platform

**Cons:**
- Triple-band only (no E6/B3) — slightly fewer satellites than ANN-MB2
- Newer product (announced Sep 2025); less field experience
- Best paired with F20P; will work with F9P but not optimized

**Verdict:** Choose this if you go with the F20P. If using F9P, the ANN-MB2 is the better match.

#### Option C: Choke-ring survey antenna (e.g., gnss.store ELT0314)

| Parameter | Value |
|---|---|
| Bands | L1/L2/L5/E1/E5a/E5b/B1/B2 (all-band) |
| Type | Choke-ring, 3D [11] |
| Connector | TNC (with 5 m TNC-SMA cable) |
| Dimensions | ~50 mm dia × 40 mm height |
| LNA | Integrated, 28 dB |
| Price | ~$150–$250 |
| Mounting | Tripod/bolt-on stand included |

**Pros:**
- **Excellent multipath rejection** — concentric rings attenuate ground reflections by 15–20 dB [4]
- **Exceptional phase center stability** — ideal for a base station
- Works with all GNSS modules (u-blox, Septentrio, Unicore, Bynav) [11]
- Includes mounting stand — no custom fabrication needed
- Best choice for the **base station** where size and weight are not constraints

**Cons:**
- Larger and heavier — not ideal for a compact rover
- TNC connector (need TNC-to-SMA adapter or a TNC-to-SMA cable)
- More expensive than patch antennas
- Overkill for the rover; the F9P/F20P will not benefit fully from the extra multipath rejection in open desert terrain

**Verdict:** **Use for the base station.** The choke-ring antenna's superior phase center stability and multipath rejection directly improve the quality of the RTCM correction data, which propagates to the rover's accuracy. For the rover, a patch antenna (Option A) is sufficient and lighter.

#### Option D: TOPGNSS AN-168G4 or similar helical/quad-filar

| Parameter | Value |
|---|---|
| Bands | L1/L2 (dual-band), some variants L1/L2/L5 |
| Type | Helical / quad-filar [13] |
| Connector | SMA |
| Price | ~$30–$80 |

**Pros:**
- 3D omnidirectional pattern — less sensitive to mounting orientation [4]
- Good multipath rejection for a mobile platform
- Inexpensive
- Available on AliExpress, TOPGNSS, various resellers

**Cons:**
- Verify it covers L2 and L5 — many cheap "RTK" antennas are L1-only and will **not** support RTK
- Less phase center stability than a patch
- Quality varies by manufacturer
- No ground plane needed, but performance still benefits from one

**Verdict:** Acceptable for the rover if a patch antenna is impractical, but verify dual/triple-band coverage before buying. Not recommended for the base station.

### 3.3 Antenna Pair Recommendation

| Role | Antenna | Why |
|---|---|---|
| **Base station** | Choke-ring (ELT0314 or equivalent) | Maximum phase center stability; the base's position error directly limits the rover's accuracy |
| **Rover** | u-blox ANN-MB2 (or ANN-MB3 for F20P) | Compact, all-band, lightweight, easy to mount |

**Total antenna budget: ~$200–$350**

### 3.4 Metal Chassis Considerations

This is a critical practical concern for a rover:

**The good news:** A metal chassis can serve as the ground plane for a patch antenna. A patch antenna mounted on or near a metal surface actually performs *better* than on a non-conductive surface, because the metal provides the required conductive ground plane [4]. This is how most automotive and industrial GNSS antennas work — they are mounted on a metal roof or body panel.

**The bad news:** If the antenna is mounted *too close* to the metal surface, or if the metal panel is part of a large conductive structure (like a chassis frame), it can cause:
- Detuning of the antenna resonance
- Increased multipath from reflections off the metal body
- Shifted phase center, especially if the chassis geometry is asymmetric

**Mitigation strategies:**

1. **Mount the antenna on a stand-off** — a 5–15 cm non-conductive (acrylic, wood, plastic) or conductive (aluminum) post that raises the antenna above the chassis. A 10 cm aluminum stand-off is a common choice [4].
2. **Add a dedicated ground plate** — a circular aluminum disc (7–15 cm diameter) mounted flat under the antenna provides a consistent, well-defined ground plane regardless of chassis geometry [4].
3. **Isolate from EMI sources** — keep the antenna at least 30 cm from motors, ESCs, battery, and 4G/LTE modules [4].
4. **Avoid carbon fiber** — carbon fiber is conductive and partially RF-shields the antenna. If the chassis is carbon fiber, insert an aluminum ground plane between the frame and the antenna [4].
5. **Calibrate the phase center offset** — after mounting, measure the exact offset from the antenna phase center to the rover's coordinate origin. This offset must be applied in the navigation software. The u-blox F9P/F20P can output the antenna's own phase center reference, but the physical mounting offset is user-defined.

**Practical setup for a URC rover:**

```
    ┌──────────────────────┐
    │   ANN-MB2 antenna    │  ← Patch antenna, sky-facing
    │   (SMA connector)    │
    └──────────┬───────────┘
               │
         ┌─────┴─────┐
         │ 10 cm AL  │  ← Aluminum stand-off (non-magnetic)
         │ stand-off │
         └─────┬────
