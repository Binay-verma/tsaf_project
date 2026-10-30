"""Date-by-date audit against declared annual government holiday schedules.
These schedules are not a reconstruction of all later ad-hoc amendments.
"""
import pandas as pd,holidays,json
from pathlib import Path
from forecasting import ROOT,STATES
# Every distinct date in annual general-holiday schedules, including named events
# explicitly omitted from printed rows because they fall on existing weekly closures.
DATES={
('Delhi',2024):'01-26 03-25 03-29 04-11 04-17 04-21 05-23 06-17 07-17 08-15 08-26 09-16 10-02 10-12 10-17 10-31 11-15 12-25',
('Delhi',2025):'01-26 02-26 03-14 03-31 04-10 04-18 05-12 06-07 07-06 08-15 08-16 09-05 10-02 10-07 10-20 11-05 12-25',
('Karnataka',2024):'01-15 01-26 03-08 03-29 04-09 04-11 04-14 04-21 05-01 05-10 06-17 07-17 08-15 09-07 09-16 10-02 10-11 10-12 10-17 10-31 11-01 11-02 11-18 12-25',
('Karnataka',2025):'01-14 01-26 02-26 03-30 03-31 04-10 04-14 04-18 04-30 05-01 06-07 07-06 08-15 08-27 09-05 09-21 10-01 10-02 10-07 10-20 10-22 11-01 11-08 12-25',
('Maharashtra',2024):'01-26 02-19 03-08 03-25 03-29 04-09 04-11 04-14 04-17 04-21 05-01 05-23 06-17 07-17 08-15 09-07 09-16 10-02 10-12 11-01 11-02 11-03 11-15 12-25',
('Maharashtra',2025):'01-26 02-19 02-26 03-14 03-30 03-31 04-06 04-10 04-14 04-18 05-01 05-12 06-07 07-06 08-15 08-27 09-05 10-02 10-21 10-22 10-23 11-05 12-25'}
SOURCES={
('Delhi',2024):'https://wcd.delhi.gov.in/sites/default/files/WCD/generic_multiple_files/holidays_2024_gnctd.pdf',
('Delhi',2025):'https://wcd.delhi.gov.in/sites/default/files/WCD/generic_multiple_files/holiday_list_2025.pdf',
('Karnataka',2024):'https://avantiscdnprodstorage.blob.core.windows.net/legalupdatedocs/29058/Government_of_Karnataka_issued_a_notification_regarding_the_holiday_list_for_2024_JAN10204.pdf',
('Karnataka',2025):'https://cag.gov.in/uploads/media/Karnataka-State-Holidays-2025-067764409e26023-56493682.pdf',
('Maharashtra',2024):'https://www.maharashtra.gov.in/site/Upload/pdf/Public_Holidays_2024.pdf',
('Maharashtra',2025):'https://www.maharashtra.gov.in/site/Upload/pdf/Maharashtra_Holiday_2025.pdf'}
DATES.update({
('Delhi',2022):'01-26 03-01 03-18 04-14 04-15 05-03 05-16 07-10 08-09 08-15 08-19 10-02 10-05 10-09 10-24 11-08 12-25',
('Delhi',2023):'01-26 03-08 03-30 04-04 04-07 04-22 05-05 06-29 07-29 08-15 09-07 09-28 10-02 10-24 10-28 11-12 11-27 12-25',
('Karnataka',2022):'01-15 01-26 03-01 04-02 04-14 04-15 05-01 05-03 07-10 08-09 08-15 08-31 09-25 10-02 10-04 10-05 10-09 10-24 10-26 11-01 11-11 12-25',
('Karnataka',2023):'01-15 01-26 02-18 03-22 04-03 04-07 04-14 04-22 04-23 05-01 06-29 07-29 08-15 09-18 09-28 10-02 10-14 10-23 10-24 10-28 11-01 11-12 11-14 11-30 12-25',
('Maharashtra',2022):'01-26 02-19 03-01 03-18 04-02 04-10 04-14 04-15 05-01 05-03 05-16 07-10 08-09 08-15 08-16 08-31 10-02 10-05 10-09 10-24 10-26 11-08 12-25',
('Maharashtra',2023):'01-26 02-18 02-19 03-07 03-22 03-30 04-04 04-07 04-14 04-22 05-01 05-05 06-28 07-29 08-15 08-16 09-19 09-28 10-02 10-24 11-12 11-14 11-15 11-27 12-25'})
SOURCES.update({
('Delhi',2022):'https://delhi.gov.in/sites/default/files/documents/Gazzeted_holiday_2022.pdf',
('Delhi',2023):'https://wcd.delhi.gov.in/sites/default/files/WCD/generic_multiple_files/holiday_list_2023_1.pdf',
('Karnataka',2022):'https://kea.co.in/wp-content/uploads/2023/04/Circular-No-152-2021-HOLIDAYS-DECLARED-BY-THE-GOVERNMENT-OF-KARNATAKA-FOR-THE-YEAR-2022.pdf',
('Karnataka',2023):'https://drive.google.com/file/d/1NZVL5wfmJQC2EFXgVKj1Bhp_g6XMdfLg/view',
('Maharashtra',2022):'https://www.fimmda.org/uploads/general/Maharashtra_State_List_Of_Holidays_2022.pdf',
('Maharashtra',2023):'https://www.maharashtra.gov.in/site/Upload/pdf/PUBLIC_HOLIDAY_2023.pdf'})
rows=[];summary=[]
for (state,year),ds in DATES.items():
 expected={pd.Timestamp(f'{year}-{d}').date() for d in ds.split()};lib=holidays.country_holidays('IN',subdiv=STATES[state],years=[year]);actual={d for d in lib if d.year==year}
 for d in sorted(expected|actual):rows.append({'state':state,'year':year,'date':str(d),'in_annual_schedule':d in expected,'in_library':d in actual,'library_name':lib.get(d,''),'status':'date_match' if d in expected&actual else 'library_extra_or_definition_difference' if d in actual else 'schedule_date_missing_from_library','primary_document':SOURCES[state,year]})
 summary.append({'state':state,'year':year,'schedule_unique_dates':len(expected),'library_dates':len(actual),'matched_dates':len(expected&actual),'schedule_only':len(expected-actual),'library_only':len(actual-expected)})
p=ROOT/'results/extended_validation';pd.DataFrame(rows).to_csv(p/'regional_calendar_date_audit.csv',index=False);pd.DataFrame(summary).to_csv(p/'regional_calendar_summary.csv',index=False)
print(pd.DataFrame(summary).to_string(index=False))
