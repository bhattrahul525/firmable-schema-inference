# Review packet (round-2 agent): validated_config

**Dataset:** SA Community Directory — SA Community (Connecting Up Inc)  
**Licence:** Creative Commons Attribution  
**File:** `sa-community-directory-2021.csv` (sha256 `a0bccc6661fe…`)

## How this ended

- Outcome **validated_config**.
- 12 model turns, 12 tool calls, $0.0134, 60.3s (download and human waits excluded). Trace: `logs/agent_runs/bench_fin2h_02/trace.jsonl`.

## Reader and record settings

- reader: `{"format": "csv", "encoding": "utf-8", "skip_rows": 0, "header_rows": 1}`
- layout: column names from raw row 1; data starts at raw row 2.
- `record_id`: hash_row (no source column)
- `observed_at`: from metadata `resource_last_modified` (one value, applies to every row)

First 12 raw rows of the file (numbered as skip_rows counts them; never held out):

1. ID_19 | Org_name | Street_Address_Line_1 | Street_Address_Line_2 | Suburb | State | Postal_Code | Country | Postal_Address_Line_1 | Postal_Address_Line_2 | Suburb | State | Postal_Code | Country | Website_1
2. 193932 | RSL Ardrossan Sub Branch | RSL Hall, West Tce | ∅ | Ardrossan | South Australia | 5571 | Australia | PO Box 133 | ∅ | Ardrossan | South Australia | 5571 | Australia | rslsa.org.au/stores/ardrossan
3. 193933 | RSL Balaklava Sub Branch | 21 Scotland St | ∅ | Balaklava | South Australia | 5461 | Australia | ∅ | ∅ | ∅ | South Australia | ∅ | Australia | www.rslsa.org.au
4. 193934 | RSL Barmera Sub Branch | ∅ | ∅ | Barmera | South Australia | 5345 | Australia | PO Box 777 | ∅ | Barmera | South Australia | 5345 | Australia | www.rslsa.org.au
5. 193935 | RSL Berri Sub Branch | 1 Strawbridge St | ∅ | Berri | South Australia | 5343 | Australia | PO Box 192 | ∅ | Berri | South Australia | 5343 | Australia | rslsa.org.au/stores/berri/#
6. 193936 | RSL Blanchetown Sub Branch | Egerton St | ∅ | Blanchetown | South Australia | 5357 | Australia | PO Box 183 | ∅ | Blanchetown | South Australia | 5357 | Australia | rslsa.org.au/stores/blanchetown
7. 193938 | RSL Bordertown Sub Branch | Cannawigra Rd | ∅ | Bordertown | South Australia | 5268 | Australia | PO Box 226 | ∅ | Bordertown | South Australia | 5268 | Australia | rslsa.org.au/stores/bordertown
8. 193939 | RSL Brighton Sub Branch | 11-13 Keelara St | ∅ | Brighton | South Australia | 5048 | Australia | PO Box 234 | ∅ | Brighton | South Australia | 5048 | Australia | www.brightonrsladelaide.com.au
9. 193940 | RSL Brinkworth, Koolunga & Yacka Sub Bra | Main St | ∅ | Brinkworth | South Australia | 5464 | Australia | PO Box 85 | ∅ | Brinkworth | South Australia | 5464 | Australia | www.bky.rslsa.org.au
10. 193942 | RSL Burra Sub Branch | 1 Market Sq | ∅ | Burra | South Australia | 5417 | Australia | PO Box 151 | ∅ | Burra | South Australia | 5417 | Australia | rslsa.org.au/stores/burra
11. 193943 | RSL Ceduna Sub Branch | ∅ | ∅ | Ceduna | South Australia | 5690 | Australia | PO Box 409 | ∅ | Ceduna | South Australia | 5690 | Australia | www.rslsa.org.au
12. 193944 | RSL Coober Pedy Sub Branch | Edward St | ∅ | Coober Pedy | South Australia | 5723 | Australia | PO Box 689 | ∅ | Coober Pedy | South Australia | 5723 | Australia | rslsa.org.au/stores/coober-pedy

## Mapped fields (config v1): mark any that are WRONG when you run `approve`

| # | Source column | → Canonical field | Transforms | Level | Evidence | Mapping conf. (model) | Parse rate (held-out) | **Field conf.** |
|---|---|---|---|---|---|---|---|---|
| 1 | `Org_name` | `entity.trading_name` | clean_whitespace | W | held_out | 0.50 | 100.0% | **0.50** |
| 2 | `Organisati_ABN` | `entity.abn` | abn | W | held_out | 0.90 | 100.0% | **0.90** |
| 3 | `Website_1` | `entity.website` | clean_whitespace | W | held_out | 0.80 | 100.0% | **0.80** |
| 4 | `Primary_Category` | `entity.industry_code` | clean_whitespace | W | held_out | 0.50 | 100.0% | **0.50** |
| 5 | `Suburb` | `address.locality` | clean_whitespace | W | held_out | 0.90 | 100.0% | **0.90** |
| 6 | `State` | `address.state` | state_code | W | held_out | 0.85 | 100.0% | **0.85** |
| 7 | `Postal_Code` | `address.postcode` | postcode | W | held_out | 0.90 | 100.0% | **0.90** |

The model's reasons per field (its words, not verified):

1. `entity.trading_name` ← `Org_name`: Organisation name in a community directory; not stated as registered name, so trading-name at low confidence.
2. `entity.abn` ← `Organisati_ABN`: Column is labelled ABN; checksum validated.
3. `entity.website` ← `Website_1`: Primary website column.
4. `entity.industry_code` ← `Primary_Category`: Directory's own category, not ANZSIC; recorded raw.
5. `address.locality` ← `Suburb`: Suburb of street address.
6. `address.state` ← `State`: State of the street address; full names like South Australia.
7. `address.postcode` ← `Postal_Code`: Postcode of street address.

## Left unmapped (not guessed)

- `ID_19`: Directory-internal id; used only as hash basis (not fully unique)
- `Street_Address_Line_1`: Not mapped to address.full: free text sometimes holds non-address labels or business names (critique c-33ed8a49)
- `Street_Address_Line_2`: Secondary street detail; not mapped to avoid partial addresses
- `Country`: Always Australia; no jurisdiction basis recorded for a constant
- `Postal_Address_Line_1`: Postal address; no postal field in ontology
- `Suburb__2`: Postal suburb; no postal field
- `State__2`: Postal state; no postal field
- `Postal_Code__2`: Postal code; no postal field
- `Country__2`: Postal country
- `Postal_Address_Line_2`: Postal address detail
- `Website_2`: Secondary website; not mapped
- `Website_3`: Secondary website; not mapped
- `Geo_Code_1_StreetAddress_`: Latitude; no geo field
- `Geo_Code_2_StreetAddress_`: Longitude; no geo field
- `Organisati_Hours`: Opening hours; no field
- `Organisati_Meetings`: Meetings; no field
- `Organisati_AGM`: AGM code; no field
- `Branch_Address_1`: Free-text branch address; nearly empty
- `Organisati_Venue_hire`: Venue description; no field
- `Organisati_Access`: Access description
- `Organisati_Disability_parking`: Accessibility; no field
- `Organisati_Access_toilets`: Accessibility; no field
- `Organisati_Wheelchair_access`: Accessibility; no field
- `Organisati_Fees`: Fees; no field
- `Contact`: Contact person; no contact field in ontology
- `Phone_1`: Phone; no contact field in ontology
- `Phone_1_comment`: Phone comment
- `Phone_3`: Phone; no field
- `Email_StreetAddress_1`: Email; no contact field in ontology
- `Email_StreetAddress_2`: Email; no field
- `Email_StreetAddress_3`: Email; no field
- `Directory_Directory_Entry_1`: Directory sub-category; not mapped
- `Directory_Directory_Entry_2`: Directory sub-category; not mapped
- `Directory_Directory_Entry_3`: Directory sub-category; not mapped
- `Organisati_Eligibility`: Eligibility text; no field
- `Organisati_Services`: Services text; no field
- `Organisati_Tag_Line`: Tagline; no field
- `Organisation_Last_updated`: Source's own last-updated stamp; observed_at uses resource metadata
- `Parent_Body`: Parent organisation; not mapped

## Needs a transform the engine does not have

- none

## Checks

- Duplicate record ids in held-out rows: {'rows': 14491, 'key': 'hash_row', 'duplicate_rows': 1, 'blank_key_rows': 0}
- Critique: The mapping is mostly sound for name, ABN, website, category, suburb, state and postcode. The main meaning error is address.full, which takes non-address text from Street_Address_Line_1 in at least two rows (Adelaide Drumming and ADRA). The remaining points are advisory: the unmapped reason for Street_Address_Line_2, record_id construction, and country handling.
  - [blocking] `address.full<-Street_Address_Line_1`: In the Adelaide Drumming row the source value is 'Locations in the City of Onkaparinga', which describes a set of locations and is not a street address. Mapping it to address.full states an address the source does not support. In the ADRA row the value is 'ADRA SA,', an organisation label, while the actual street ('31 Prospect Rd') sits in Street_Address_Line_2. The mapped value there is not the street address. (suggested: Make address.full conditional so it maps only rows whose Street_Address_Line_1 holds a street address (for example by excluding non-address text), or drop the field for this column. Map Street_Address_Line_2 to address.full where it holds the street, or document why it is left out.)
  - [advisory] `Street_Address_Line_2`: Street_Address_Line_2 is listed as unmapped with the reason 'Secondary address detail'. In the ADRA row it holds the actual street address, so the stated reason does not match the data. (suggested: Revisit the unmapped reason. Consider a conditional mapping of Street_Address_Line_2 to address.full for rows where Line 1 is not a street address.)
  - [advisory] `address.full<-Street_Address_Line_1`: In the Goodstart row the value includes the business name ('Goodstart Early Learning Plympton, 247-251 Anzac Hwy'). The street part is correct, but the claim includes non-address text. (suggested: Accept as a source-stated value with a caveat, or parse out the street portion with a transform that removes text without adding any.)
  - [advisory] `record_id`: record_id uses hash_row=true, but ID_19 appears to be a unique directory-internal identifier on every row shown. Rule 15 prefers a check_unique column when one exists. (suggested: If ID_19 is confirmed unique across the file, use record_id on ID_19 with check_unique and keep hash_row only as a fallback.)
  - [advisory] `address.country`: Country is unmapped as 'Always Australia'. The directory's own metadata may support a constant for the jurisdiction, but no basis is recorded for it. (suggested: Leave address.country unmapped unless the dataset metadata or title states that the directory covers every row. If it does, document that basis in a constant mapping anchored on a column filled on every row.)

## Examples (raw → value, held-out rows)

- `entity.trading_name<-Org_name`: `South Australian Weightlifting Club` → `South Australian Weightlifting Club`; `Ladies, Friends and Fellowship Group` → `Ladies, Friends and Fellowship Group`; `Morgan Medical Clinic` → `Morgan Medical Clinic`
- `entity.abn<-Organisati_ABN`: `39266279756` → `39266279756`; `25560728917` → `25560728917`; `93799021552` → `93799021552`
- `entity.website<-Website_1`: `www.saweightliftingclub.com.au` → `www.saweightliftingclub.com.au`; `www.loxtonshow.org.au` → `www.loxtonshow.org.au`; `www.police.sa.gov.au` → `www.police.sa.gov.au`
- `entity.industry_code<-Primary_Category`: `Recreation` → `Recreation`; `Health & Disability` → `Health & Disability`; `Community Organisation & Development` → `Community Organisation & Development`
- `address.locality<-Suburb`: `Kidman` → `Kidman`; `Renmark` → `Renmark`; `Morgan` → `Morgan`
- `address.state<-State`: `South Australia` → `SA`; `Victoria` → `VIC`
- `address.postcode<-Postal_Code`: `5025` → `5025`; `5341` → `5341`; `5320` → `5320`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
