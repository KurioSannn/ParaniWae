# Literature Review - Technology, Learning, and Pencak Silat

**Purpose:** establish the prior-art baseline and guard against unsupported novelty claims. This is a focused desk review, not a registered systematic review.

## 1. UNESCO cultural heritage foundation

UNESCO (2019), *Traditions of Pencak Silat*, Representative List of the Intangible Cultural Heritage of Humanity, element 01391.

Key points from the UNESCO element description:
- pencak silat includes sporting, mental-spiritual, self-defence, and artistic dimensions;
- regional differences exist in movement, styles, music/accompaniment, costume, instruments, and traditional weapons;
- teaching occurs in non-formal schools and includes oral traditions, greetings, philosophical phrases, rhymed poems, advice, songs, and instrument techniques;
- practitioners are taught to protect themselves and others, avoid harm, and build comradeship.

URL: https://ich.unesco.org/en/RL/traditions-of-pencak-silat-01391

## 2. Technology and learning studies

### 2.1 Nuriman (2018) - digital motion capture of Silat Tuo

Nuriman, H. (2018). Gerak digital Silat Tuo Minangkabau melalui pemanfaatan teknologi motion capture. *The Journal of Society and Media, 2*(2), 109-120. https://doi.org/10.26740/jsm.v2n2.p109-120

Contribution reported: documents Silat Tuo/Silat Harimau movements through motion capture and explores applying motion data to 3D models for preservation, education, and performance. The abstract argues that movement databases can support learning beyond constraints of time and place.

Implication: a digital movement archive is not by itself a unique contribution. SILATARA should add partner governance, learning feedback, and measurable transfer to real practice.

### 2.2 Muktiani et al. (2022) - AR/multimedia learning

Muktiani, N. R., Soegiyanto, Siswantoyo, Rahayu, S., & Hermawan, H. A. (2022). Augmented reality mobile app-based multimedia learning of pencak silat to enhance the junior high school students' learning outcomes. *Cakrawala Pendidikan, 41*(2). https://doi.org/10.21831/cp.v41i2.49217

Contribution reported: development of mobile AR-based multimedia learning using an R&D process. The study evaluates learning media and student learning outcomes.

Implication: multimedia/AR education is prior art. SILATARA's differentiator should be its specific movement assessment, partner-approved correction, and community connection, not “digital learning” alone.

### 2.3 Rahmawati et al. (2023) - CNN movement classification

Rahmawati, V. N., Yuniarto, E. M., & Nugroho, S. M. S. (2023). Pencak silat movement classification using CNN based on body pose. *Journal of Advanced Research in Electrical Engineering (JAREE), 7*(2). https://doi.org/10.12962/jaree.v7i2.369

Contribution reported: body-pose keypoints are extracted and used as input to a CNN for frame-level movement recognition/classification.

Implication: do not claim that body-pose-based classification in pencak silat is new.

### 2.4 Sinulingga et al. (2024) - systematic literature review

Sinulingga, A., Kasih, I., Hasibuan, S., Daulay, D. E., & Abdullah, N. M. (2024). Unveiling technology's integral role in pencak silat: A systematic literature review. *Journal Sport Area, 9*(1), 20-29. https://doi.org/10.25299/sportarea.2024.vol9(1).14700

The review searches Scopus and Web of Science and synthesizes a selected set of studies on technology in pencak silat. It discusses digital learning and technology approaches including interactive multimedia, AR/VR, motion-capture-related work, RFID, and other sports/education systems.

Implication: technology integration in pencak silat already has a research history. The review itself notes the need for more work on implementation, accessibility, and supporting learners/coaches in identifying movement shortcomings.

### 2.5 Sulistyaningsih (2025) - neural-network pose detection thesis

Sulistyaningsih, E. (2025). *Deteksi pose jurus 1 tangan kosong kategori tunggal Ikatan Pencak Silat Indonesia menggunakan neural network* [Undergraduate thesis, Politeknik Negeri Jember]. https://sipora.polije.ac.id/41994/

The repository record describes MediaPipe pose landmark extraction and experiments using MLP and CNN for jurus tunggal pose detection. The reported results include an MLP validation accuracy of 85% and a generalization issue when tested with new videos; the CNN experiment is reported as overfitting. Verify exact experimental tables in the thesis PDF before quoting precise metrics in a formal paper.

Implication: user-independent generalization and data split design are critical.

### 2.6 Ratnadewi et al. (2026) - Ibing Penca angle-based pose analysis

Ratnadewi, R., Prijono, A., Hangkawidjaja, A. D., Rustiyanti, S., & Al Badri, D. (2026). Angle-based pose analysis for digital documentation and learning support of Ibing Penca stances in Pencak Silat. *Journal of Applied Science, Engineering, Technology, and Education, 8*(1), 102-118. https://doi.org/10.35877/454RI.asci4539

Published online 30 April 2026. The paper describes classifying 62 Ibing Penca stances using MediaPipe's 33 body keypoints and six body/foot angles. It reports 95.2% successful classification (58 of 62) and recommends more movement variation and improved detection in more diverse conditions.

Implication: MediaPipe-based stance classification, angle calculation, and independent learning for Ibing Penca are already published. Avoid claiming these methods are new.

### 2.7 Batubara (2026) - web-based single-artistic-jurus scoring

Batubara, F. N. (2026). *Modernisasi sistem penilaian jurus seni tunggal pencak silat berbasis web menggunakan metode pose estimation* [Undergraduate thesis, Universitas Muhammadiyah Sumatera Utara]. https://repository.umsu.ac.id/handle/123456789/32364

The repository metadata dates the work 10 October 2026. Its abstract describes MediaPipe Pose, joint-angle calculation, movement sequence/transition analysis, duration, automatic score calculation, results, and rankings. The abstract reports 1,845 of 1,867 reference frames had valid joint angles (98.8%). The system is described as an assessment aid; artistic aspects still require human judgement.

Implication: a web-based pose-estimation score for pencak silat single artistic routine is also prior art. SILATARA's novelty must not be framed as “first web-based scoring app”.

## 3. Research gap synthesis

The sources above suggest the following defensible development opportunities. They are gaps in the reviewed work, not proof that no other product/research has done them:

1. **Partner-governed cultural provenance:** movement and knowledge items carry origin, instructor, permission, scope, review date, and version.
2. **Style-specific assessment configuration:** standards are attached to one tradition/partner, not universalized.
3. **Explainable correction tied to an instructional phase:** the system does not stop at classifying a stance or showing a score.
4. **Quality-aware assessment:** it detects when input is not assessable and explains camera/visibility issues rather than returning false precision.
5. **Integrated cultural learning and practice:** historical/contextual learning is connected to real movement practice and instructor attribution.
6. **Learning and participation outcomes:** the platform tests whether AI-supported practice improves movement learning, confidence, cultural understanding, and later participation in real schools.
7. **Partner value:** schools/instructors have attribution, content control, and potential economic benefits.

## 4. Proposed research questions

- RQ1: How reliably can browser-based pose/hand landmarks support assessment of a partner-approved beginner movement set under defined camera conditions?
- RQ2: How closely do AI component assessments agree with instructor assessments for each approved movement and rubric version?
- RQ3: Does AI-assisted feedback improve beginner movement learning relative to video-only instruction in a controlled pilot?
- RQ4: Does a low-pressure digital learning entry point improve cultural awareness, confidence, and intention to attend an in-person class?
- RQ5: What governance and benefit-sharing practices make instructors/partners willing to contribute and maintain cultural learning content?

## 5. Methodological cautions

- A 95.2% result from an Ibing Penca dataset is not comparable to SILATARA's score unless datasets, units of analysis, movement definitions, and testing conditions match.
- Split evaluation data by participant, not just by video/frame, to reduce identity leakage.
- Keep a held-out participant test set and record device/camera conditions.
- Use more than raw accuracy: macro-F1, per-class recall, confusion matrix, not-assessable rate, calibration, expert agreement, and confidence intervals.
- For angle measurements, only report MAE if a reliable reference measurement exists and coordinate/calibration methods are documented.
- Use an instructor panel for inter-rater agreement; preserve disagreements and adjudication notes.
- Treat learning-effectiveness and social-impact studies as separate from model-performance tests.
