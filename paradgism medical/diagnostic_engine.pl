% ============================================================
%  diagnostic_engine.pl — Prolog inference engine
%
%  Called by prolog_bridge.py via subprocess.
%  Python pre-asserts known/2 facts and batch_mode/0;
%  any unasserted symptom defaults to 'unknown'.
% ============================================================

:- dynamic known/2.
:- dynamic batch_mode/0.
:- use_module(library(lists)).

% ── Knowledge base ───────────────────────────────────────────
:- consult('diagnosis.pl').
:- consult('symptoms_descriptions.pl').
:- consult('solutions.pl').


% ── Symptom resolution ───────────────────────────────────────
%
%  known/2 is asserted by Python before running any goal.
%  Unasserted symptoms fall through to the batch default (unknown).

% Batch fallback — unasserted symptom is unknown, not absent
known(_, unknown) :-
    batch_mode, !.


% ── Question bank ─────────────────────────────────────────────
%  Maps symptom atoms to natural language questions.
%  Used by prolog_bridge.py to fetch question text for the GUI.

symptom_question(high_blood_pressure,
    'Have you been told you have high blood pressure, or do you regularly measure above 140/90?').
symptom_question(high_fever,
    'Do you have a high fever (above 39 C / 102 F)?').
symptom_question(mild_fever,
    'Do you have a mild fever or feel slightly warm?').
symptom_question(cough,
    'Do you have a cough?').
symptom_question(fatigue,
    'Are you feeling unusually tired or fatigued?').
symptom_question(headache,
    'Do you have a headache?').
symptom_question(nausea,
    'Are you experiencing nausea?').
symptom_question(vomiting,
    'Have you been vomiting?').
symptom_question(diarrhoea,
    'Are you experiencing diarrhea?').
symptom_question(skin_rash,
    'Do you have a skin rash?').
symptom_question(itching,
    'Are you experiencing itching?').
symptom_question(joint_pain,
    'Do you have joint pain or aching joints?').
symptom_question(chest_pain,
    'Are you experiencing chest pain or tightness?').
symptom_question(breathlessness,
    'Do you have difficulty breathing or shortness of breath?').
symptom_question(dizziness,
    'Are you feeling dizzy or lightheaded?').
symptom_question(back_pain,
    'Do you have back pain?').
symptom_question(abdominal_pain,
    'Do you have abdominal or stomach pain?').
symptom_question(stomach_pain,
    'Do you have stomach pain?').
symptom_question(runny_nose,
    'Do you have a runny nose?').
symptom_question(continuous_sneezing,
    'Are you sneezing frequently?').
symptom_question(chills,
    'Are you experiencing chills?').
symptom_question(shivering,
    'Are you shivering?').
symptom_question(sweating,
    'Are you sweating excessively?').
symptom_question(weight_loss,
    'Have you experienced unexplained weight loss recently?').
symptom_question(yellowish_skin,
    'Has your skin or the whites of your eyes turned yellow?').
symptom_question(dark_urine,
    'Is your urine unusually dark in colour?').
symptom_question(loss_of_appetite,
    'Have you lost your appetite?').
symptom_question(constipation,
    'Are you experiencing constipation?').
symptom_question(polyuria,
    'Are you urinating more frequently than usual?').
symptom_question(burning_micturition,
    'Do you experience burning or pain when urinating?').
symptom_question(fast_heart_rate,
    'Is your heart beating unusually fast?').
symptom_question(blurred_and_distorted_vision,
    'Is your vision blurred or distorted?').
symptom_question(swelling_joints,
    'Are your joints swollen?').
symptom_question(phlegm,
    'Are you coughing up phlegm or mucus?').
symptom_question(blood_in_sputum,
    'Have you noticed blood in your cough or sputum?').
symptom_question(throat_irritation,
    'Do you have a sore or irritated throat?').
symptom_question(swelled_lymph_nodes,
    'Do you have swollen lymph nodes (lumps in neck, armpit, or groin)?').
symptom_question(malaise,
    'Do you have a general feeling of being unwell?').
symptom_question(dehydration,
    'Do you feel dehydrated or excessively thirsty?').
symptom_question(indigestion,
    'Are you experiencing indigestion or heartburn?').
symptom_question(muscle_pain,
    'Do you have muscle pain or body aches?').
symptom_question(neck_pain,
    'Do you have pain in your neck?').
symptom_question(stiff_neck,
    'Is your neck stiff or hard to turn?').
symptom_question(weakness_in_limbs,
    'Do you have significant weakness in your arms or legs?').
symptom_question(spinning_movements,
    'Do you experience a spinning or rotating sensation?').
symptom_question(loss_of_balance,
    'Do you have difficulty maintaining your balance?').
symptom_question(weight_gain,
    'Have you experienced unexplained weight gain recently?').
symptom_question(anxiety,
    'Are you experiencing significant anxiety or worry?').
symptom_question(depression,
    'Are you feeling persistently depressed or hopeless?').
symptom_question(acidity,
    'Are you experiencing acid reflux or burning in the chest?').
symptom_question(pain_behind_the_eyes,
    'Do you have pain or pressure behind your eyes?').
symptom_question(nodal_skin_eruptions,
    'Do you have raised or nodular skin eruptions?').
symptom_question(dischromic__patches,
    'Do you have discoloured or patchy areas of skin?').
symptom_question(movement_stiffness,
    'Do you have stiffness that limits your movement?').
symptom_question(pus_filled_pimples,
    'Do you have pus-filled pimples or cysts on your skin?').
symptom_question(cold_hands_and_feets,
    'Do your hands and feet feel unusually cold?').
symptom_question(enlarged_thyroid,
    'Is your thyroid gland (front of neck) swollen or enlarged?').
symptom_question(swelling_of_stomach,
    'Is your stomach or abdomen noticeably swollen or distended?').
symptom_question(mood_swings,
    'Do you experience significant mood swings?').
symptom_question(restlessness,
    'Are you feeling unusually restless or unable to sit still?').
symptom_question(lethargy,
    'Do you feel lethargic -- slow to move or think?').
symptom_question(irregular_sugar_level,
    'Have you had irregular blood sugar readings?').
symptom_question(excessive_hunger,
    'Are you experiencing excessive hunger even after eating?').
symptom_question(palpitations,
    'Are you aware of your heartbeat -- does it feel like it is racing or pounding?').
symptom_question(history_of_alcohol_consumption,
    'Do you have a history of heavy or regular alcohol consumption?').
symptom_question(extra_marital_contacts,
    'Have you had unprotected sexual contact with multiple partners?').
symptom_question(receiving_blood_transfusion,
    'Have you recently received a blood transfusion?').
symptom_question(bruising,
    'Do you bruise easily or notice unexplained bruises?').
symptom_question(cramps,
    'Do you experience muscle cramps?').
symptom_question(blister,
    'Do you have fluid-filled blisters on your skin?').
symptom_question(prominent_veins_on_calf,
    'Can you see prominent or bulging veins on your calves?').
symptom_question(swollen_legs,
    'Are your legs swollen, particularly around the ankles?').
symptom_question(pain_in_anal_region,
    'Do you have pain in or around the anal region?').
symptom_question(irritation_in_anus,
    'Do you have irritation or itching around the anus?').
symptom_question(skin_peeling,
    'Is your skin peeling or flaking?').
symptom_question(yellow_crust_ooze,
    'Do you have yellow crusting or oozing sores on your skin?').
symptom_question(muscle_weakness,
    'Is your muscle strength noticeably reduced?').
symptom_question(watering_from_eyes,
    'Are your eyes watering excessively?').
symptom_question(redness_of_eyes,
    'Are your eyes red or irritated?').
symptom_question(patches_in_throat,
    'Do you have white patches or spots in your throat?').
symptom_question(mucoid_sputum,
    'Are you producing thick, mucus-like sputum?').


% ── Red-flag symptoms (NEWS2 escalation triggers) ────────────────────────────
%  These are clinically urgent symptoms that jump to the front of the queue
%  when the NEWS2 score is elevated.

:- dynamic red_flag/1.

red_flag(chest_pain).
red_flag(breathlessness).
red_flag(weakness_in_limbs).
red_flag(altered_sensorium).
red_flag(blood_in_sputum).
red_flag(stiff_neck).

get_red_flags(Flags) :- findall(F, red_flag(F), Flags).


% ── Question text lookup ──────────────────────────────────────────────────────
%  get_question(+Symptom, -Text): returns question text for a symptom atom.
%  Falls back to a generic question if no specific text is defined.

get_question(Symptom, Text) :-
    symptom_question(Symptom, Text), !.
get_question(Symptom, Text) :-
    atom_string(Symptom, S),
    split_string(S, "_", "", Parts),
    atomic_list_concat(Parts, ' ', Display),
    format(atom(Text), 'Do you have ~w?', [Display]).


% ── Follow-up symptom chains ─────────────────────────────────────────────────
%
%  follow_up(+Confirmed, ?FollowUp)
%  When a symptom is confirmed, these related symptoms should be asked next.
%  Ordered by clinical relevance (most discriminating first).

follow_up(high_blood_pressure, headache).
follow_up(high_blood_pressure, chest_pain).
follow_up(high_blood_pressure, dizziness).
follow_up(high_blood_pressure, blurred_and_distorted_vision).
follow_up(cough,               blood_in_sputum).
follow_up(cough,               phlegm).
follow_up(cough,               mucoid_sputum).
follow_up(cough,               breathlessness).
follow_up(high_fever,          chills).
follow_up(high_fever,          sweating).
follow_up(high_fever,          shivering).
follow_up(mild_fever,          chills).
follow_up(skin_rash,           itching).
follow_up(skin_rash,           blister).
follow_up(skin_rash,           nodal_skin_eruptions).
follow_up(abdominal_pain,      nausea).
follow_up(abdominal_pain,      vomiting).
follow_up(abdominal_pain,      diarrhoea).
follow_up(abdominal_pain,      loss_of_appetite).
follow_up(stomach_pain,        nausea).
follow_up(stomach_pain,        vomiting).
follow_up(headache,            stiff_neck).
follow_up(headache,            blurred_and_distorted_vision).
follow_up(headache,            dizziness).
follow_up(chest_pain,          breathlessness).
follow_up(chest_pain,          fast_heart_rate).
follow_up(chest_pain,          sweating).
follow_up(dizziness,           loss_of_balance).
follow_up(dizziness,           spinning_movements).
follow_up(dizziness,           nausea).
follow_up(yellowish_skin,      dark_urine).
follow_up(yellowish_skin,      itching).
follow_up(yellowish_skin,      loss_of_appetite).
follow_up(joint_pain,          swelling_joints).
follow_up(joint_pain,          movement_stiffness).
follow_up(burning_micturition, polyuria).
follow_up(fatigue,             weight_loss).
follow_up(fatigue,             loss_of_appetite).
follow_up(nausea,              vomiting).
follow_up(vomiting,            diarrhoea).
follow_up(vomiting,            dehydration).
follow_up(breathlessness,      chest_pain).
follow_up(itching,             skin_rash).
follow_up(dark_urine,          yellowish_skin).
follow_up(blood_in_sputum,     breathlessness).
follow_up(blood_in_sputum,     chest_pain).
follow_up(throat_irritation,   patches_in_throat).
follow_up(throat_irritation,   phlegm).
follow_up(runny_nose,          continuous_sneezing).
follow_up(runny_nose,          throat_irritation).
follow_up(sweating,            chills).
follow_up(weight_loss,         loss_of_appetite).
follow_up(loss_of_appetite,    nausea).
follow_up(polyuria,            excessive_hunger).
follow_up(polyuria,            weight_loss).
follow_up(swelling_joints,     movement_stiffness).

%  get_follow_ups(+Symptom, -FollowUps): return all follow-ups as a list
get_follow_ups(Symptom, FollowUps) :-
    findall(F, follow_up(Symptom, F), FollowUps).


% ── Exclusion rules ───────────────────────────────────────────────────────────
%
%  excludes(+DeniedSymptom, ?SkipSymptom)
%  When DeniedSymptom is answered NO, SkipSymptom becomes clinically
%  irrelevant and should be removed from the screening queue.

% Respiratory — blood/phlegm in sputum require a cough to produce them
excludes(cough,          blood_in_sputum).
excludes(cough,          phlegm).
excludes(cough,          mucoid_sputum).

% Nasal — continuous sneezing almost always accompanies a runny nose
excludes(runny_nose,     continuous_sneezing).

% Skin — nodal eruptions are a subtype of skin rash
excludes(skin_rash,      nodal_skin_eruptions).

% Jaundice cluster — dark urine in this context is a consequence of yellowish skin
excludes(yellowish_skin, dark_urine).

% Urinary — burning micturition and bladder discomfort share the same cluster
excludes(burning_micturition, bladder_discomfort).

% Fever cluster — shivering without any fever is rare as a primary complaint
excludes(high_fever,     shivering).
excludes(mild_fever,     shivering).

% GI — passage of gases is only significant alongside abdominal symptoms
excludes(abdominal_pain, passage_of_gases).
excludes(stomach_pain,   passage_of_gases).

% Eye — watering eyes unlikely if eyes are not red or irritated
excludes(redness_of_eyes, watering_from_eyes).

%  get_exclusions(+DeniedSymptom, -Excluded): return all symptoms to skip
get_exclusions(Symptom, Excluded) :-
    findall(E, excludes(Symptom, E), Excluded).


% ── Disease-symptom knowledge base (decision tree scoring) ───────────────────
%
%  disease_symptom(+Disease, +Symptom)
%  One fact per (disease, symptom) pair — the expected symptom profile
%  for each disease. Used only by the decision tree; diagnosis/1 rules
%  remain the authoritative inference source.

disease_symptom(fungal_infection,           itching).
disease_symptom(fungal_infection,           skin_rash).
disease_symptom(fungal_infection,           nodal_skin_eruptions).
disease_symptom(fungal_infection,           dischromic__patches).
disease_symptom(allergy,                    continuous_sneezing).
disease_symptom(allergy,                    shivering).
disease_symptom(allergy,                    chills).
disease_symptom(allergy,                    watering_from_eyes).
disease_symptom(allergy,                    skin_rash).
disease_symptom(gerd,                       acidity).
disease_symptom(gerd,                       indigestion).
disease_symptom(gerd,                       vomiting).
disease_symptom(gerd,                       cough).
disease_symptom(gerd,                       chest_pain).
disease_symptom(chronic_cholestasis,        itching).
disease_symptom(chronic_cholestasis,        vomiting).
disease_symptom(chronic_cholestasis,        yellowish_skin).
disease_symptom(chronic_cholestasis,        nausea).
disease_symptom(chronic_cholestasis,        loss_of_appetite).
disease_symptom(drug_reaction,              itching).
disease_symptom(drug_reaction,              skin_rash).
disease_symptom(drug_reaction,              stomach_pain).
disease_symptom(drug_reaction,              vomiting).
disease_symptom(peptic_ulcer_diseae,        vomiting).
disease_symptom(peptic_ulcer_diseae,        loss_of_appetite).
disease_symptom(peptic_ulcer_diseae,        abdominal_pain).
disease_symptom(peptic_ulcer_diseae,        passage_of_gases).
disease_symptom(aids,                       muscle_wasting).
disease_symptom(aids,                       patches_in_throat).
disease_symptom(aids,                       high_fever).
disease_symptom(aids,                       extra_marital_contacts).
disease_symptom(diabetes,                   fatigue).
disease_symptom(diabetes,                   weight_loss).
disease_symptom(diabetes,                   restlessness).
disease_symptom(diabetes,                   lethargy).
disease_symptom(diabetes,                   irregular_sugar_level).
disease_symptom(diabetes,                   polyuria).
disease_symptom(diabetes,                   excessive_hunger).
disease_symptom(gastroenteritis,            vomiting).
disease_symptom(gastroenteritis,            sunken_eyes).
disease_symptom(gastroenteritis,            dehydration).
disease_symptom(gastroenteritis,            diarrhoea).
disease_symptom(bronchial_asthma,           fatigue).
disease_symptom(bronchial_asthma,           cough).
disease_symptom(bronchial_asthma,           high_fever).
disease_symptom(bronchial_asthma,           breathlessness).
disease_symptom(bronchial_asthma,           mucoid_sputum).
disease_symptom(bronchial_asthma,           phlegm).
disease_symptom(hypertension,               high_blood_pressure).
disease_symptom(hypertension,               headache).
disease_symptom(hypertension,               chest_pain).
disease_symptom(hypertension,               dizziness).
disease_symptom(hypertension,               loss_of_balance).
disease_symptom(hypertension,               lack_of_concentration).
disease_symptom(migraine,                   acidity).
disease_symptom(migraine,                   indigestion).
disease_symptom(migraine,                   headache).
disease_symptom(migraine,                   blurred_and_distorted_vision).
disease_symptom(migraine,                   excessive_hunger).
disease_symptom(cervical_spondylosis,       back_pain).
disease_symptom(cervical_spondylosis,       weakness_in_limbs).
disease_symptom(cervical_spondylosis,       neck_pain).
disease_symptom(cervical_spondylosis,       dizziness).
disease_symptom(cervical_spondylosis,       loss_of_balance).
disease_symptom(paralysis_brain_hemorrhage, vomiting).
disease_symptom(paralysis_brain_hemorrhage, headache).
disease_symptom(paralysis_brain_hemorrhage, weakness_in_limbs).
disease_symptom(paralysis_brain_hemorrhage, altered_sensorium).
disease_symptom(paralysis_brain_hemorrhage, stiff_neck).
disease_symptom(jaundice,                   itching).
disease_symptom(jaundice,                   vomiting).
disease_symptom(jaundice,                   fatigue).
disease_symptom(jaundice,                   weight_loss).
disease_symptom(jaundice,                   high_fever).
disease_symptom(jaundice,                   yellowish_skin).
disease_symptom(jaundice,                   dark_urine).
disease_symptom(malaria,                    chills).
disease_symptom(malaria,                    vomiting).
disease_symptom(malaria,                    high_fever).
disease_symptom(malaria,                    sweating).
disease_symptom(malaria,                    headache).
disease_symptom(malaria,                    nausea).
disease_symptom(malaria,                    muscle_pain).
disease_symptom(chicken_pox,               itching).
disease_symptom(chicken_pox,               skin_rash).
disease_symptom(chicken_pox,               fatigue).
disease_symptom(chicken_pox,               lethargy).
disease_symptom(chicken_pox,               high_fever).
disease_symptom(chicken_pox,               headache).
disease_symptom(chicken_pox,               loss_of_appetite).
disease_symptom(chicken_pox,               blister).
disease_symptom(dengue,                     skin_rash).
disease_symptom(dengue,                     headache).
disease_symptom(dengue,                     high_fever).
disease_symptom(dengue,                     chills).
disease_symptom(dengue,                     joint_pain).
disease_symptom(dengue,                     vomiting).
disease_symptom(dengue,                     fatigue).
disease_symptom(dengue,                     pain_behind_the_eyes).
disease_symptom(typhoid,                    chills).
disease_symptom(typhoid,                    vomiting).
disease_symptom(typhoid,                    fatigue).
disease_symptom(typhoid,                    headache).
disease_symptom(typhoid,                    nausea).
disease_symptom(typhoid,                    constipation).
disease_symptom(typhoid,                    abdominal_pain).
disease_symptom(typhoid,                    high_fever).
disease_symptom(hepatitis_a,                joint_pain).
disease_symptom(hepatitis_a,                vomiting).
disease_symptom(hepatitis_a,                yellowish_skin).
disease_symptom(hepatitis_a,                dark_urine).
disease_symptom(hepatitis_a,                nausea).
disease_symptom(hepatitis_a,                loss_of_appetite).
disease_symptom(hepatitis_a,                abdominal_pain).
disease_symptom(hepatitis_b,                itching).
disease_symptom(hepatitis_b,                fatigue).
disease_symptom(hepatitis_b,                lethargy).
disease_symptom(hepatitis_b,                yellowish_skin).
disease_symptom(hepatitis_b,                dark_urine).
disease_symptom(hepatitis_b,                loss_of_appetite).
disease_symptom(hepatitis_b,                abdominal_pain).
disease_symptom(hepatitis_c,                fatigue).
disease_symptom(hepatitis_c,                yellowish_skin).
disease_symptom(hepatitis_c,                nausea).
disease_symptom(hepatitis_c,                loss_of_appetite).
disease_symptom(hepatitis_c,                yellowing_of_eyes).
disease_symptom(hepatitis_d,                joint_pain).
disease_symptom(hepatitis_d,                vomiting).
disease_symptom(hepatitis_d,                fatigue).
disease_symptom(hepatitis_d,                high_fever).
disease_symptom(hepatitis_d,                yellowish_skin).
disease_symptom(hepatitis_d,                dark_urine).
disease_symptom(hepatitis_d,                nausea).
disease_symptom(hepatitis_e,                joint_pain).
disease_symptom(hepatitis_e,                vomiting).
disease_symptom(hepatitis_e,                fatigue).
disease_symptom(hepatitis_e,                high_fever).
disease_symptom(hepatitis_e,                yellowish_skin).
disease_symptom(hepatitis_e,                dark_urine).
disease_symptom(hepatitis_e,                nausea).
disease_symptom(alcoholic_hepatitis,        vomiting).
disease_symptom(alcoholic_hepatitis,        yellowish_skin).
disease_symptom(alcoholic_hepatitis,        abdominal_pain).
disease_symptom(alcoholic_hepatitis,        swelling_of_stomach).
disease_symptom(alcoholic_hepatitis,        history_of_alcohol_consumption).
disease_symptom(tuberculosis,               chills).
disease_symptom(tuberculosis,               vomiting).
disease_symptom(tuberculosis,               fatigue).
disease_symptom(tuberculosis,               weight_loss).
disease_symptom(tuberculosis,               cough).
disease_symptom(tuberculosis,               high_fever).
disease_symptom(tuberculosis,               breathlessness).
disease_symptom(tuberculosis,               sweating).
disease_symptom(tuberculosis,               blood_in_sputum).
disease_symptom(common_cold,                continuous_sneezing).
disease_symptom(common_cold,                chills).
disease_symptom(common_cold,                fatigue).
disease_symptom(common_cold,                cough).
disease_symptom(common_cold,                headache).
disease_symptom(common_cold,                runny_nose).
disease_symptom(common_cold,                throat_irritation).
disease_symptom(pneumonia,                  chills).
disease_symptom(pneumonia,                  fatigue).
disease_symptom(pneumonia,                  cough).
disease_symptom(pneumonia,                  high_fever).
disease_symptom(pneumonia,                  breathlessness).
disease_symptom(pneumonia,                  sweating).
disease_symptom(pneumonia,                  malaise).
disease_symptom(pneumonia,                  phlegm).
disease_symptom(pneumonia,                  chest_pain).
disease_symptom(dimorphic_hemorrhoids_piles, constipation).
disease_symptom(dimorphic_hemorrhoids_piles, pain_in_anal_region).
disease_symptom(dimorphic_hemorrhoids_piles, bloody_stool).
disease_symptom(dimorphic_hemorrhoids_piles, irritation_in_anus).
disease_symptom(heart_attack,               vomiting).
disease_symptom(heart_attack,               sweating).
disease_symptom(heart_attack,               chest_pain).
disease_symptom(heart_attack,               breathlessness).
disease_symptom(varicose_veins,             fatigue).
disease_symptom(varicose_veins,             cramps).
disease_symptom(varicose_veins,             bruising).
disease_symptom(varicose_veins,             obesity).
disease_symptom(varicose_veins,             swollen_legs).
disease_symptom(varicose_veins,             prominent_veins_on_calf).
disease_symptom(hypothyroidism,             fatigue).
disease_symptom(hypothyroidism,             weight_gain).
disease_symptom(hypothyroidism,             cold_hands_and_feets).
disease_symptom(hypothyroidism,             mood_swings).
disease_symptom(hypothyroidism,             lethargy).
disease_symptom(hypothyroidism,             depression).
disease_symptom(hypothyroidism,             enlarged_thyroid).
disease_symptom(hyperthyroidism,            fatigue).
disease_symptom(hyperthyroidism,            mood_swings).
disease_symptom(hyperthyroidism,            weight_loss).
disease_symptom(hyperthyroidism,            restlessness).
disease_symptom(hyperthyroidism,            sweating).
disease_symptom(hyperthyroidism,            diarrhoea).
disease_symptom(hyperthyroidism,            fast_heart_rate).
disease_symptom(hypoglycemia,               fatigue).
disease_symptom(hypoglycemia,               vomiting).
disease_symptom(hypoglycemia,               anxiety).
disease_symptom(hypoglycemia,               sweating).
disease_symptom(hypoglycemia,               headache).
disease_symptom(hypoglycemia,               nausea).
disease_symptom(hypoglycemia,               blurred_and_distorted_vision).
disease_symptom(hypoglycemia,               dizziness).
disease_symptom(osteoarthristis,            joint_pain).
disease_symptom(osteoarthristis,            neck_pain).
disease_symptom(osteoarthristis,            knee_pain).
disease_symptom(osteoarthristis,            hip_joint_pain).
disease_symptom(osteoarthristis,            swelling_joints).
disease_symptom(osteoarthristis,            painful_walking).
disease_symptom(arthritis,                  muscle_weakness).
disease_symptom(arthritis,                  swelling_joints).
disease_symptom(arthritis,                  movement_stiffness).
disease_symptom(arthritis,                  loss_of_appetite).
disease_symptom(arthritis,                  joint_pain).
disease_symptom(vertigo_paroxysmal_positional_vertigo, headache).
disease_symptom(vertigo_paroxysmal_positional_vertigo, loss_of_balance).
disease_symptom(vertigo_paroxysmal_positional_vertigo, nausea).
disease_symptom(vertigo_paroxysmal_positional_vertigo, vomiting).
disease_symptom(vertigo_paroxysmal_positional_vertigo, dizziness).
disease_symptom(vertigo_paroxysmal_positional_vertigo, spinning_movements).
disease_symptom(vertigo_paroxysmal_positional_vertigo, unsteadiness).
disease_symptom(acne,                       skin_rash).
disease_symptom(acne,                       pus_filled_pimples).
disease_symptom(acne,                       blackheads).
disease_symptom(acne,                       scurring).
disease_symptom(urinary_tract_infection,    burning_micturition).
disease_symptom(urinary_tract_infection,    bladder_discomfort).
disease_symptom(urinary_tract_infection,    foul_smell_of_urine).
disease_symptom(urinary_tract_infection,    continuous_feel_of_urine).
disease_symptom(psoriasis,                  skin_rash).
disease_symptom(psoriasis,                  joint_pain).
disease_symptom(psoriasis,                  skin_peeling).
disease_symptom(psoriasis,                  silver_like_dusting).
disease_symptom(psoriasis,                  small_dents_in_nails).
disease_symptom(psoriasis,                  inflammatory_nails).
disease_symptom(impetigo,                   skin_rash).
disease_symptom(impetigo,                   blister).
disease_symptom(impetigo,                   red_sore_around_nose).
disease_symptom(impetigo,                   yellow_crust_ooze).
disease_symptom(flu,                        high_fever).
disease_symptom(flu,                        cough).
disease_symptom(flu,                        fatigue).
disease_symptom(flu,                        headache).
disease_symptom(flu,                        chills).
disease_symptom(flu,                        sweating).
disease_symptom(flu,                        muscle_pain).


% ── Decision tree predicates ──────────────────────────────────────────────────
%
%  At each step the tree picks the symptom that best splits the remaining
%  candidate diseases — i.e. closest to a 50/50 split across candidates.
%  Score = present_count * absent_count  (maximised at equal split).

% All distinct symptoms in the knowledge base
all_candidate_symptoms(Symptoms) :-
    findall(S, disease_symptom(_, S), Ss),
    sort(Ss, Symptoms).

% A disease is still a candidate if fewer than half its expected symptoms
% have been explicitly denied by the patient.
is_candidate(Denied, Disease) :-
    disease_symptom(Disease, _),
    findall(S, disease_symptom(Disease, S), Profile),
    findall(S, (member(S, Profile), member(S, Denied)), DeniedMatches),
    length(Profile,      Total),
    length(DeniedMatches, NDenied),
    Total > 0,
    NDenied * 2 < Total.

% Information gain score for one symptom across the candidate set.
symptom_score(Candidates, Symptom, Score) :-
    findall(D, (member(D, Candidates), disease_symptom(D, Symptom)), Matching),
    length(Matching,  Present),
    length(Candidates, Total),
    Absent is Total - Present,
    Score is Present * Absent.

% best_next_question(+Asked, -BestSymptom)
%
%  Uses known/2 facts (already asserted by the Python bridge) to derive
%  the confirmed and denied sets, then picks the highest-scoring unasked
%  symptom.  Fails if no useful question remains.
best_next_question(Asked, BestSymptom) :-
    % atom(S) guards against the batch_mode fallback clause known(_, unknown)
    % firing with an unbound S, which would corrupt the candidate set.
    findall(S, (known(S, no), atom(S)), Denied),
    findall(D, is_candidate(Denied, D), RawCandidates),
    sort(RawCandidates, Candidates),
    Candidates \= [],
    all_candidate_symptoms(AllSymptoms),
    subtract(AllSymptoms, Asked, Unasked),
    Unasked \= [],
    findall(Score-Sym,
            ( member(Sym, Unasked),
              symptom_score(Candidates, Sym, Score),
              Score > 0 ),
            Pairs),
    Pairs \= [],
    max_member(_-BestSymptom, Pairs).


% ── Diagnostic entry points ──────────────────────────────────

% First match wins; cut stops backtracking after one disease
diagnose(Disease) :-
    diagnosis(Disease), !.
diagnose(unknown).

% Collect all matching diseases via exact dataset rules (deduped)
diagnose_all(Diseases) :-
    findall(D, diagnosis(D), Raw),
    sort(Raw, Diseases).

% ── Partial-match diagnosis (used by prolog_bridge.py in batch mode) ─────────
%
%  diagnose_partial(-Diseases)
%
%  Uses the disease_symptom/2 knowledge base rather than the dataset-derived
%  diagnosis/1 rules.  A disease is a candidate if at least 2 of its expected
%  symptoms have been confirmed (known(S, yes)).  This allows Prolog to reason
%  over partial symptom sets — the typical case in an interactive consultation.

disease_confirmed_count(Disease, Count) :-
    findall(S, (disease_symptom(Disease, S), known(S, yes)), Confirmed),
    length(Confirmed, Count).

diagnose_partial(Diseases) :-
    findall(D, disease_symptom(D, _), AllRaw),
    sort(AllRaw, AllDiseases),
    findall(D,
            ( member(D, AllDiseases),
              disease_confirmed_count(D, Count),
              Count >= 2 ),
            Diseases).


