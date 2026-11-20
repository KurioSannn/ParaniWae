# TRIA Repository Snapshot Audit

**Source:** `reference-materials/TRIA_gitingest.md` supplied by the user.  
**Scope:** source snapshot only; not a complete history of TRIA and not an independent audit of the deployed production system.

## 1. Visible architecture in the digest

The digest describes a repository with:
- Django web application (`tria-master/` in the setup notes),
- FastAPI service (`backend/`) for a score endpoint,
- Next.js landing page (`landing/`),
- dance catalog/tutorial/assessment/result templates,
- a sanggar directory and authentication modules.

The project description lists catalogues, tutorial videos, camera-based assessment screens, sanggar directories, user accounts, and progress/result pages.

## 2. Important code observations

In the included `backend/main.py` section, the endpoint `/api/givescore` generates a score using `random.randint(70, 95)`. It then requests generic textual feedback from an OpenAI chat completion. If the API errors, the fallback still returns a random score and canned feedback.

In the included `dance_assessment.html` section, the browser asks for camera permission through `navigator.mediaDevices.getUserMedia`, starts a timer, plays a YouTube tutorial, and updates sub-movement instructions according to elapsed time. At the end, it calls the score API and stores results in session storage.

The gitingest digest's stack/landing descriptions mention MediaPipe/OpenPose, TensorFlow/scikit-learn, Flutter, FastAPI, Google Cloud Platform, and Firebase Firestore. However, text searches within this snapshot did not reveal active pose-landmark extraction, `pose_landmarks`, `cv2` processing, or an integrated MediaPipe implementation in the inspected code. The `backend/main.py` score is random, not calculated from submitted pose landmarks in the displayed endpoint.

## 3. What SILATARA should learn from this audit

- Do not treat a live camera preview and a scoring API as proof of computer-vision assessment.
- Do not generate random scores or generic feedback and label them AI movement analysis.
- If MediaPipe is named in UI/marketing, it must be integrated and demonstrable in the actual code path.
- Score logic must use measured landmarks, defined phases, an approved rubric, and quality gates.
- Every assessment result must include a trace to the movement ID, partner/style, rubric version, reference version, and technical quality status.
- Keep marketing copy aligned with the actual implementation status.

## 4. Important limitation

This audit does not prove that the original TRIA team never implemented MediaPipe elsewhere, that their competition demo behaved exactly like the snapshot, or that the provided digest contains every file/version. Phrase conclusions as “in the supplied repository snapshot, the visible implementation...” rather than claims about the team or deployed product as a whole.
