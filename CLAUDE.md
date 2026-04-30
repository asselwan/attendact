# Noshight (AttendAct)

## Integrated Patterns

- **Visit regularity scoring** — `ml/features.py:_visit_regularity()`. Coefficient of variation of inter-visit intervals. Regular visitors (low CV) are less likely to no-show. New features: visit_regularity, reschedule_count, is_rescheduled, is_new_patient. Ported from predict-appointment-noshow (scout-refs/noshight/) automated feature engineering.
- **v3 heuristic weights** — `ml/heuristic.py`. Added visit_regularity (0.05), reschedule_count (0.03), is_new_patient (0.03) weights to the additive scorer. Irregular visitors, frequent reschedulers, and first-timers get elevated risk scores.

## Scout Reference Repos

Study these repos at `~/Apps/scout-refs/noshight/` for patterns to integrate:

- **Medical-Appointment-No-Show-Prediction** — Full ML pipeline: feature engineering, XGBoost, AWS deployment. Steal: feature engineering (scheduling-to-appointment interval, historical no-show rate) for Noshight's heuristic scorer and XGBoost graduation.
- **medical-appointment-no-shows** — LightGBM predictor with Flask + Docker. LightGBM often outperforms XGBoost. Steal: model approach and Docker deployment pattern for FastAPI.
- **predict-appointment-noshow** — Automated feature engineering with Featuretools. Steal: automated feature discovery for features Noshight hasn't considered.
- **sample-appointment-reminders-node** — Twilio SMS appointment reminder system. The intervention side of no-show prevention. Noshight predicts, this acts.
- **SMS-Appointment-Reminder-Webapp** — SMS reminder with Celery task queue. Steal: scheduled reminder task queue pattern for Noshight's engagement layer.
