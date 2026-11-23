# Person 6, Mesbah: Front Matter, Chapter 4, Chapter 5, Appendices and Assembly

See the [review index](README.md) for the shared vocabulary. Severity: High blocks submission or contradicts the evidence; Medium affects consistency; Low is polish.

## Front matter

| # | Severity | Where (quoted) | Problem | What we need |
|---|---|---|---|---|
| F1 | High | "ABSTRACT" followed directly by "TABLE OF CONTENTS" | The abstract is empty. | Write it last (problem, proposed response, scope, contribution), in the word range the supervisor confirms, with "proposed" wording. |
| F2 | High | List of Figures | No Figures 3-1 to 3-34. | Refresh the field in Word (Ctrl+A, then F9, "Update entire table"). |
| F3 | High | List of Tables | No Tables 3-1, 3-2 or 3-39 to 3-48. | Refresh after Joe adds Tables 3-1 and 3-2. |
| F4 | High | Table of Contents: "3. METHODOLOGY AND PROPOSED WORK 20", "4. SYSTEM PROTOTYPE 62" | Chapter level only, and the page numbers are out of date: Chapter 4 now starts near page 117. | Refresh; consider heading levels 1 to 3 and Appendices A to D. |
| F5 | High | Cover | No submission month and year, degree line or department. | Confirm the real details; never guess them. |
| F6 | High | Declaration: "Bachelor of Science in ____________________" | Blank degree; all six signatures and dates blank. | Fill the degree; collect signatures and dates. |
| F7 | Medium | Cover "Youssef Ibrahem Gamal Aldin" vs declaration "Youssef Ibrahim Gamal" | Two spellings and lengths of one name. | One official spelling everywhere, including Appendix B. |
| F8 | Medium | Cover order "Marwan, Ali / Youssef, Belal / Mahmoud, Yassin" vs declaration "Marwan, Youssef / Yassin, Ali / Belal, Mahmoud" | Author order differs. | Agree one order. |
| F9 | Medium | Cover: "We watch over a city in its worst hours" | A slogan used as the subtitle, at odds with the report's proposal tone. | A descriptive subtitle, or none. |
| F10 | Medium | Declaration: "I hereby certify that this material, which I now submit" | First person singular for six students. | Ask the supervisor whether each student signs a separate page. |
| F11 | Medium | Acknowledgment: "built the mapping prototype" | Mentions only the prototype. | List the real contributions. |
| F12 | Medium | List of Acronyms | Missing acronyms used in the report: UML, SOS, xBD, SARD, ERD, API, CNN, RLS. Some listed ones appear once only. | Rebuild the list from the merged text. |
| F13 | Low | Captions "Table 1-1 Intended audience", "Table 4-1.", "Figure 4-1.", "Table 2-1:" | Three caption styles. | Colon style everywhere: "Table 4-1: ...". |

## Chapter 4 System Prototype

The chapter is honest. It says the display gives no damage classes, confidence scores or verified building findings, and it reports no accuracy numbers.

| # | Severity | Where (quoted) | Problem | What we need |
|---|---|---|---|---|
| P1 | High | "Confirm the draft requirement links when the requirements are approved." | An editorial note inside body text. "the 23 November 2026 requirements draft" ties the chapter to a draft. | Remove the note; cite Section 3.2. |
| P2 | High | "view a preliminary change layer ... under the baseline method" | The baseline (differencing, threshold, alignment of the two images) is never described, so the overlay cannot be judged. | Two sentences on how the mask is computed. |
| P3 | High | Table 4-1 "Pre-event acquisition 26 July 2022"; "Post-event ... 28 February 2023, 22 days after" | The dates are not traceable to evidence. | Confirm from the Maxar metadata and give the scene IDs. |
| P4 | High | "These steps inform the Project II work discussed in Chapter 5." | Chapter 5 is empty. | Resolves when Chapter 5 is written. |
| P5 | Medium | Table 4-2 "FR-DC-04 and FR-DC-12. Area comparison and pixel-change overlay" marked Partial | FR-DC-04 and FR-DC-12 are building-level (selected building, damage grade). The prototype is area-level. | "Related behaviour only, not covered". |
| P6 | Medium | Table 4-2 "FR-MR-01 and FR-MR-04" | FR-MR-01 needs a stitched orthomosaic over a base map; the prototype uses satellite crops. | Add "no orthomosaic" to the boundary column. |
| P7 | Medium | Table 4-2 rows "Assistance cases, person tracking, and hazards" and "Route guidance" citing FR-MR-08 | FR-MR-08 is matched only by legend symbols the text calls placeholders. OBJ-03 to OBJ-06, F5 Compound Hazard Alerts and restoration cost are not shown as uncovered. | "None" for FR IDs; list OBJ-03 to OBJ-06, F5 and cost as not covered. |
| P8 | Medium | Captions Figure 4-1 to 4-6 | They do not say whether each image is a screenshot of a running page or a generated output (Figure 4-6 is an output). | "Screenshot of ..." or "Output image ...". |
| P9 | Medium | "Imagery: Maxar Open Data Program [21]"; Table 4-1 "CC BY-NC 4.0" | Minimal credit; the licence is non-commercial, which matters for the market text in Chapter 2 and Appendix C. | Use Maxar's required credit line once; note the non-commercial limit. |
| P10 | Medium | "Python scripts prepared browser views using Folium and Leaflet" | Readers may take this as the platform stack. | One sentence: the prototype tooling is separate from the platform design in Section 3.3. |
| P11 | Low | "It demonstrates a practical 2D comparison workflow" | "practical" is unsupported (no user evaluation). | "a 2D comparison view". |
| P12 | Low | "The pre-event and post-event labels illustrate the distinction in draft requirement FR-IM-02." | The scene browser is a Maxar listing, not a capture session. | "resembles". |
| P13 | Low | Table 4-2 | The dashboard, mobile scaffold and report template in `person6_plan.md` (P-6 to P-8) are not mentioned. | One sentence that they are not presented as evidence. |
| P14 | Low | "Reviewer" | Sections 3.2 and 3.3 use Analyst and Commander. | Use the role names. |

## Chapter 5 (with Yassin)

The chapter has headings only. The content plan and inputs are in [person1_yassin.md](person1_yassin.md#chapter-5-with-mesbah).

## Appendices

| # | Severity | Where (quoted) | Problem | What we need |
|---|---|---|---|---|
| A1 | High | "Appendix A: Extended Tables" | Empty. | Fill it (the Section 3.3 data dictionary is ready: `docs/documentation/chapter5/appendix_data_dictionary.md`) or delete it. |
| A2 | High | Table B-1 "Ali (Person 5) ... Section 3.3 system design is in progress." | Out of date; Section 3.3 is complete. Rows mix first names and "Person N". | Update the statuses and use one naming style. |
| A3 | Medium | Appendix C "Figure C-1 summarises the analysis" | Check that the SWOT figure is inserted. | Confirm. |
| A4 | Medium | "EDITORIAL TRACKER (DELETE BEFORE SUBMISSION)" | Internal tracker at the end of the report. | Remove before submission. |

Appendix C content issues belong to Mahmoud (see [person4_mahmoud.md](person4_mahmoud.md)), and Appendix D issues to Bela (see [person2_bela.md](person2_bela.md)).

## Final assembly checklist

- [ ] Section 3.1 received and merged; numbering of Figure 3-1 and Tables 3-1, 3-2 confirmed.
- [ ] Contents, List of Figures and List of Tables refreshed.
- [ ] One caption style in every chapter.
- [ ] Acronyms rebuilt and defined at first use.
- [ ] Cover, declaration and names confirmed; signatures collected.
- [ ] Chapter 5 and abstract written.
- [ ] Editorial tracker and all "[P# ...]" placeholders removed.
- [ ] Supervisor decisions recorded (see the [review index](README.md)).
