# Review packet (round-2 agent): partial_config

**Dataset:** SA Community Directory — SA Community (Connecting Up Inc)  
**Licence:** Creative Commons Attribution  
**File:** `sa-community-directory-2021.csv` (sha256 `a0bccc6661fe…`)

## How this ended

- Outcome **partial_config**, ended by the harness: finish refused 2 times in a row.
- 8 model turns, 8 tool calls, $0.1676, 46.56s (download and human waits excluded). Trace: `logs/agent_runs/bench_fin2s_02/trace.jsonl`.

## Reader and record settings

- reader: `{"format": "csv", "encoding": "utf-8-sig", "skip_rows": 0, "header_rows": 1}`
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
| 1 | `Org_name` | `entity.legal_name` | clean_whitespace | W | held_out | 0.60 | 100.0% | **0.60** |
| 2 | `Organisati_ABN` | `entity.abn` | regex_replace({'pattern': '\\s', 'repl': ''}) → abn | P | held_out | 0.90 | 98.2% | **0.90** |
| 3 | `Website_1` | `entity.website` | clean_whitespace | W | held_out | 0.80 | 100.0% | **0.80** |
| 4 | `Suburb` | `address.locality` | clean_whitespace | W | held_out | 0.85 | 100.0% | **0.85** |
| 5 | `State` | `address.state` | state_code | W | held_out | 0.85 | 100.0% | **0.85** |
| 6 | `Postal_Code` | `address.postcode` | postcode | W | held_out | 0.85 | 100.0% | **0.85** |

The model's reasons per field (its words, not verified):

1. `entity.legal_name` ← `Org_name`: organisation name in directory
2. `entity.abn` ← `Organisati_ABN`: ABN column
3. `entity.website` ← `Website_1`: website
4. `address.locality` ← `Suburb`: street suburb
5. `address.state` ← `State`: street state
6. `address.postcode` ← `Postal_Code`: street postcode

## Left unmapped (not guessed)

- `ID_19`: not unique
- `Other columns`: contact, access, hours, postal address and descriptive columns not mapped
- `Branch_Address_1`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Contact`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Country`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Country__2`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Directory_Directory_Entry_1`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Directory_Directory_Entry_2`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Directory_Directory_Entry_3`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Email_StreetAddress_1`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Email_StreetAddress_2`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Email_StreetAddress_3`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Geo_Code_1_StreetAddress_`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Geo_Code_2_StreetAddress_`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Organisati_AGM`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Organisati_Access`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Organisati_Access_toilets`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Organisati_Disability_parking`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Organisati_Eligibility`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Organisati_Fees`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Organisati_Hours`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Organisati_Meetings`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Organisati_Services`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Organisati_Tag_Line`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Organisati_Venue_hire`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Organisati_Wheelchair_access`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Organisation_Last_updated`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Parent_Body`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Phone_1`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Phone_1_comment`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Phone_3`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Postal_Address_Line_1`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Postal_Address_Line_2`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Postal_Code__2`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Primary_Category`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `State__2`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Street_Address_Line_1`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Street_Address_Line_2`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Suburb__2`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Website_2`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column
- `Website_3`: abstained by the harness (failed validation or an unanswered critique issue): the agent did not account for this column

## Needs a transform the engine does not have

- none

## Abstentions (fields removed, with reasons)

- `column:Branch_Address_1`: failed validation when the harness ended the run
- `column:Contact`: failed validation when the harness ended the run
- `column:Country`: failed validation when the harness ended the run
- `column:Country__2`: failed validation when the harness ended the run
- `column:Directory_Directory_Entry_1`: failed validation when the harness ended the run
- `column:Directory_Directory_Entry_2`: failed validation when the harness ended the run
- `column:Directory_Directory_Entry_3`: failed validation when the harness ended the run
- `column:Email_StreetAddress_1`: failed validation when the harness ended the run
- `column:Email_StreetAddress_2`: failed validation when the harness ended the run
- `column:Email_StreetAddress_3`: failed validation when the harness ended the run
- `column:Geo_Code_1_StreetAddress_`: failed validation when the harness ended the run
- `column:Geo_Code_2_StreetAddress_`: failed validation when the harness ended the run
- `column:Organisati_AGM`: failed validation when the harness ended the run
- `column:Organisati_Access`: failed validation when the harness ended the run
- `column:Organisati_Access_toilets`: failed validation when the harness ended the run
- `column:Organisati_Disability_parking`: failed validation when the harness ended the run
- `column:Organisati_Eligibility`: failed validation when the harness ended the run
- `column:Organisati_Fees`: failed validation when the harness ended the run
- `column:Organisati_Hours`: failed validation when the harness ended the run
- `column:Organisati_Meetings`: failed validation when the harness ended the run
- `column:Organisati_Services`: failed validation when the harness ended the run
- `column:Organisati_Tag_Line`: failed validation when the harness ended the run
- `column:Organisati_Venue_hire`: failed validation when the harness ended the run
- `column:Organisati_Wheelchair_access`: failed validation when the harness ended the run
- `column:Organisation_Last_updated`: failed validation when the harness ended the run
- `column:Parent_Body`: failed validation when the harness ended the run
- `column:Phone_1`: failed validation when the harness ended the run
- `column:Phone_1_comment`: failed validation when the harness ended the run
- `column:Phone_3`: failed validation when the harness ended the run
- `column:Postal_Address_Line_1`: failed validation when the harness ended the run
- `column:Postal_Address_Line_2`: failed validation when the harness ended the run
- `column:Postal_Code__2`: failed validation when the harness ended the run
- `column:Primary_Category`: failed validation when the harness ended the run
- `column:State__2`: failed validation when the harness ended the run
- `column:Street_Address_Line_1`: failed validation when the harness ended the run
- `column:Street_Address_Line_2`: failed validation when the harness ended the run
- `column:Suburb__2`: failed validation when the harness ended the run
- `column:Website_2`: failed validation when the harness ended the run
- `column:Website_3`: failed validation when the harness ended the run

## Checks

- Duplicate record ids in held-out rows: {'rows': 14491, 'key': 'hash_row', 'duplicate_rows': 1, 'blank_key_rows': 0}
- Critique: The main problem is that Org_name is mapped to legal_name even though the directory never says the names are registered and many rows are shops, markets or programs. It should go to trading_name at low confidence. The other mappings are broadly sound, with minor completeness caveats.
  - [blocking] `entity.legal_name<-Org_name`: Org_name comes from a community directory, not a regulator register, and nothing in the data says it is the registered name. Many values are not registered entities: 'RSPCA Op Shop - Brighton' (a shop), 'Port Elliot Rotary Market' (an event), 'Ryan Mitchell Swim Centre' (a council facility), 'Multiple Sclerosis Society Peer Support Group - Southern', and a Centacare service program. Their parent bodies are in Parent_Body. Rule 5 says any other name column maps to trading_name at 0.6 or lower, not legal_name. (suggested: Map Org_name to entity.trading_name with mapping_confidence of 0.6 or lower. Do not map it to legal_name.)
  - [advisory] `entity.abn<-Organisati_ABN`: The ABN is mapped correctly with the abn transform, but where the row is a facility of a parent body (e.g. Eldercare Evanston Park, ABN 63758127271, parent Eldercare Inc.), the ABN may belong to the parent rather than the named row. (suggested: Keep the mapping and lower mapping_confidence slightly.)
  - [advisory] `address.state<-State`: In the Centacare row the street State and Suburb are blank, and the row has only a postal address (State__2, Suburb__2). Postal_Code (5608) is therefore mapped without a street suburb or state, which leaves the address incomplete. (suggested: Accept the gap, or note that postal fields are not mapped.)
  - [advisory] `unmapped`: The 'Other columns' entry is too vague for rule 3. Organisation_Last_updated is a per-row statement date that could support observed_at. Parent_Body, the contact columns and the category columns are all lumped together. (suggested: List each column with its own reason. Consider using Organisation_Last_updated as the per-row observed_at, parsed with parse_date.)
- Critique: No blocking errors: the mapped fields (name, ABN, website, locality, state, postcode) match what the columns hold. Concerns are advisory: legal_name confidence for a directory source, ABN possibly belonging to a parent, and incomplete column accounting.
  - [advisory] `entity.legal_name<-Org_name`: Org_name is a community directory listing name, not labelled as the registered name, and the dataset is not a regulator register. Many values are not registered entities but venues, shops, programs or sub-units (e.g. 'RSPCA Op Shop - Brighton', 'Port Elliot Rotary Market', 'Ryan Mitchell Swim Centre', 'Centacare ... Homelessness Service (Youth Focus)'). Under rule 5 these should be trading_name at 0.6 or lower, or legal_name at 0.7 or lower. (suggested: Keep the mapping but set mapping_confidence to 0.6 or lower, or map to entity.trading_name. Note that the names are directory listing names.)
  - [advisory] `entity.abn<-Organisati_ABN`: The ABN is the ABN of the organisation that owns the listing, not necessarily of the named venue or sub-unit. For example, Eldercare Evanston Park carries an ABN that probably belongs to the parent, Eldercare Inc. The ABN mapping is correct and follows the abn transform rule. (suggested: Keep the abn mapping with moderate confidence. Optionally note that ABN may belong to a parent body.)
  - [advisory] `address.locality<-Suburb`: Suburb may not reflect a street address. In the MS Society example the Suburb value 'Onkaparinga' is a council area rather than a suburb. The Street_Address_Line columns are unmapped, so no address.full is produced. (suggested: Optionally map the Street_Address_Line_1 and Street_Address_Line_2 columns to address.full or leave them unmapped with a reason. Lower the confidence for locality.)
  - [advisory] `unmapped`: Many columns are listed as 'abstained by the harness', so they are not properly accounted for with real reasons. Parent_Body, Primary_Category, Organisation_Last_updated and Website_2/3 are examples. The Primary_Category and Directory columns could be industry_code under rule 9. (suggested: Give each column a real reason, or map Primary_Category as industry_code with raw source value. Organisation_Last_updated is not a valid_from date, since it is a listing update.)

## Examples (raw → value, held-out rows)

- `entity.legal_name<-Org_name`: `RSL Moonta Sub Branch` → `RSL Moonta Sub Branch`; `Table Tennis SA Inc.` → `Table Tennis SA Inc.`; `Monash Tennis Club` → `Monash Tennis Club`
- `entity.website<-Website_1`: `rslsa.org.au/stores/moonta-rsl` → `rslsa.org.au/stores/moonta-rsl`; `www.tabletennissa.org.au` → `www.tabletennissa.org.au`; `www.waikeriegolf.com.au` → `www.waikeriegolf.com.au`
- `address.locality<-Suburb`: `Moonta` → `Moonta`; `Adelaide` → `Adelaide`; `Monash` → `Monash`
- `address.state<-State`: `South Australia` → `SA`; `Victoria` → `VIC`
- `address.postcode<-Postal_Code`: `5558` → `5558`; `5342` → `5342`; `5322` → `5322`
- `entity.abn<-Organisati_ABN`: `87122159712` → `87122159712`; `16 944 372 531` → `16944372531`; `95234142798` → `95234142798`
---
To review: `python -m src.part2_agent.approve <source_id>`. This file does not approve anything.
