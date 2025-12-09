// In static/script.js
document.addEventListener('DOMContentLoaded', () => {

    // --- 1. Snowy Animation ---
    const canvas = document.getElementById('snowCanvas');
    if (canvas) { 
        const ctx = canvas.getContext('2d');
        let snowflakes = [];

        const isOnIndex = document.querySelector('.btn-valora-login') !== null;

        let numSnowflakes, maxRadius, maxSpeedY;

        if (isOnIndex) {
            // Original settings for Index Page
            numSnowflakes = 100; // More snowflakes
            maxRadius = 3.0;     // Max 3px radius
            maxSpeedY = 2.0;     // Max 2.0 speed
        } else {
            // Slower and Smaller for all other pages (Questionnaire, Recommendations)
            numSnowflakes = 70;  // Fewer snowflakes
            maxRadius = 1.5;     // Max 1.5px radius
            maxSpeedY = 0.8;     // Max 0.8 speed
        }

        function setCanvasSize() {
            canvas.width = window.innerWidth;
            canvas.height = window.innerHeight;
        }
        window.addEventListener('resize', setCanvasSize);
        setCanvasSize();

        function createSnowflake() {
            return {
                x: Math.random() * canvas.width,
                y: Math.random() * canvas.height,
                radius: Math.random() * maxRadius + 0.5,
                speedX: Math.random() * 0.5 - 0.25,
                speedY: Math.random() * maxSpeedY + 0.2,
                opacity: Math.random() * 0.7 + 0.3
            };
        }

        function initSnowflakes() {
            for (let i = 0; i < numSnowflakes; i++) {
                snowflakes.push(createSnowflake());
            }
        }

        function drawSnowflakes() {
            ctx.clearRect(0, 0, canvas.width, canvas.height);
            snowflakes.forEach(flake => {
                ctx.beginPath();
                ctx.arc(flake.x, flake.y, flake.radius, 0, Math.PI * 2);
                ctx.fillStyle = `rgba(255, 255, 255, ${flake.opacity})`;
                ctx.fill();
            });
        }

        function updateSnowflakes() {
            snowflakes.forEach(flake => {
                flake.x += flake.speedX;
                flake.y += flake.speedY;
                if (flake.y > canvas.height + flake.radius) {
                    flake.y = -flake.radius;
                    flake.x = Math.random() * canvas.width;
                    flake.speedX = Math.random() * 0.5 - 0.25;
                }
                if (flake.x > canvas.width + flake.radius) {
                    flake.x = -flake.radius;
                } else if (flake.x < -flake.radius) {
                    flake.x = canvas.width + flake.radius;
                }
            });
        }

        function animateSnow() {
            updateSnowflakes();
            drawSnowflakes();
            requestAnimationFrame(animateSnow);
        }

        initSnowflakes();
        animateSnow();
    }


    // --- 2. Logic for Questionnaire Page ---
    const panasArea = document.getElementById('panas-area');
    if (panasArea) {
        // --- Get all the Page sections ---
        const questionnaireWrapper = document.getElementById('questionnaire-wrapper');
        const loadingMessage = document.getElementById('calculating-mood-loading');
        
        // Page 1: PANAS
        const questionDisplay = document.getElementById('question-display');
        const progressBar = document.getElementById('progress-bar');
        const progressIndicator = document.getElementById('progress-indicator');
        const specialMessage = document.getElementById('special-message');
        const nextButton = document.getElementById('next-to-sam-btn');
        const ratingNumbers = document.querySelectorAll('.rating-number');

        // Page 2: SAM Valence
        const valencePage = document.getElementById('valence-page');
        const valenceRadios = document.querySelectorAll('input[name="valence"]');

        // Page 3: SAM Arousal
        const arousalPage = document.getElementById('arousal-page');
        const samForm = document.getElementById('sam-form'); // Form on the last page
        
        // --- PANAS Setup ---
        const questions = [
            "Interested", "Excited", "Strong", "Enthusiastic", "Proud",
            "Alert", "Inspired", "Determined", "Attentive", "Active",
            "Distressed", "Upset", "Guilty", "Scared", "Hostile",
            "Irritable", "Ashamed", "Nervous", "Jittery", "Afraid"
        ];
        const positiveAdjectives = ["Interested", "Excited", "Strong", "Enthusiastic", "Proud", "Alert", "Inspired", "Determined", "Attentive", "Active"];
        const negativeAdjectives = ["Distressed", "Upset", "Guilty", "Scared", "Hostile", "Irritable", "Ashamed", "Nervous", "Jittery", "Afraid"];

        let currentQuestionIndex = 0;
        let panasScores = {}; // Stores the 20 PANAS scores
        let samValenceScore = null; // Will store the single valence score

        function shuffleArray(array) {
            for (let i = array.length - 1; i > 0; i--) {
                const j = Math.floor(Math.random() * (i + 1));
                [array[i], array[j]] = [array[j], array[i]];
            }
            return array;
        }

        // This function displays the 20 PANAS questions
        function displayQuestion() {
            if (currentQuestionIndex < questions.length) {
                const question = questionOrder[currentQuestionIndex];
                questionDisplay.innerHTML = `I feel: <strong>${question}</strong>`;
                
                progressBar.value = currentQuestionIndex;
                progressIndicator.textContent = `${currentQuestionIndex + 1} / ${questions.length}`;
                
                ratingNumbers.forEach(n => n.classList.remove('selected'));
                
                if (currentQuestionIndex === questions.length - 1) {
                    nextButton.style.display = 'inline-block';
                } else {
                    nextButton.style.display = 'none';
                }

                if (currentQuestionIndex === 17) {
                    specialMessage.textContent = "Just a little bit more to go..";
                } else {
                    specialMessage.textContent = "";
                }
            }
        }
        
        // Listener for the 1-5 PANAS rating numbers
        ratingNumbers.forEach(number => {
            number.addEventListener('click', () => {
                const value = parseInt(number.dataset.value);
                panasScores[questionOrder[currentQuestionIndex]] = value;
                ratingNumbers.forEach(n => n.classList.remove('selected'));
                number.classList.add('selected');

                if (currentQuestionIndex < questions.length - 1) {
                    currentQuestionIndex++;
                    setTimeout(() => {
                        displayQuestion();
                    }, 200);
                }
            });
        });

        // Listener for the "Next" button (after PANAS)
        nextButton.addEventListener('click', () => {
            const lastQuestionKey = questionOrder[currentQuestionIndex];
            if (!panasScores[lastQuestionKey]) {
                alert("Please select a rating for the last question.");
                return;
            }
            
            progressBar.value = questions.length;
            progressIndicator.textContent = `${questions.length} / ${questions.length}`;

            // --- Hide PANAS, Show SAM Valence ---
            panasArea.style.display = 'none';
            valencePage.style.display = 'block';
            window.scrollTo(0, 0); 
        });

        // --- NEW: Listener for Valence Radios ---
        valenceRadios.forEach(radio => {
            radio.addEventListener('click', function() {
                // Save the score
                samValenceScore = parseFloat(this.value);

                // --- Hide Valence, Show Arousal ---
                valencePage.style.display = 'none';
                arousalPage.style.display = 'block';
                window.scrollTo(0, 0);
            });
        });

        // Listener for the FINAL submit button (after SAM Arousal)
        samForm.addEventListener('submit', (event) => {
            event.preventDefault(); // Stop form from submitting
            
            // Get the *last* score (arousal)
            const samArousalScoreRadio = document.querySelector('input[name="arousal"]:checked');

            if (!samValenceScore) {
                alert("A valence score is missing. Please restart."); // Safety check
                return;
            }
            if (!samArousalScoreRadio) {
                alert("Please select a rating for your energy level.");
                return;
            }

            const samArousalScore = parseFloat(samArousalScoreRadio.value);

            // Hide SAM form and show the final loading message
            arousalPage.style.display = 'none';
            loadingMessage.style.display = 'block';

            // Now, calculate the combined mood
            finishQuestionnaire(samValenceScore, samArousalScore);
        });


        function finishQuestionnaire(samV, samA) {
            // --- 1. Calculate PANAS Scores ---
            let totalPositive = 0;
            positiveAdjectives.forEach(adj => { totalPositive += panasScores[adj] || 0; });
            let totalNegative = 0;
            negativeAdjectives.forEach(adj => { totalNegative += panasScores[adj] || 0; });

            const panasValence = totalPositive - totalNegative; 
            const panasArousal = (totalPositive + totalNegative) / 20.0; 

            // --- 2. Normalize SAM Scores ---
            const samValenceNormalized = (samV - 5) * 10; 
            const samArousalNormalized = ((samA - 1) * (4 / 8)) + 1;

            // --- 3. Average the scores ---
            const finalValence = (panasValence + samValenceNormalized) / 2;
            const finalArousal = (panasArousal + samArousalNormalized) / 2;
            
            // --- 4. Determine mood based on *final* (averaged) scores ---
            let userMood;
            if (finalValence >= 0 && finalArousal > 2.5) userMood = "Happy/Energetic";
            else if (finalValence >= 0 && finalArousal <= 2.5) userMood = "Calm/Peaceful";
            else if (finalValence < 0 && finalArousal > 2.5) userMood = "Angry/Tense";
            else userMood = "Sad/Melancholy";
                
            // --- 5. Redirect after a short delay ---
            setTimeout(() => {
                window.location.href = `/recommendations?mood=${encodeURIComponent(userMood)}`;
            }, 500);
        }

        // Start the questionnaire
        let questionOrder = shuffleArray([...questions]);
        displayQuestion();
    }
    
    // --- 3. Logic for Recommendations Page ---
    const recommendationsList = document.getElementById('recommendations-list');
    if (recommendationsList) {
        
        let currentRecommendationIds = [];
        const addAllButton = document.getElementById('add-all-btn');
        const addAllStatus = document.getElementById('add-all-status');
        
        async function fetchRecommendations() {
            const loadingDiv = document.getElementById('loading');
            const msgP = document.getElementById('recommendation-message');
            const mood = document.getElementById('mood-display').textContent;
            
            if (loadingDiv) loadingDiv.style.display = 'block';
            if (msgP) msgP.textContent = `Finding songs for an '${mood}' mood...`;
            recommendationsList.innerHTML = '';
            if (addAllButton) addAllButton.style.display = 'none'; 
            if (addAllStatus) addAllStatus.textContent = '';


            try {
                const response = await fetch('/get_recommendations', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        mood: mood
                    }),
                });
                
                if (loadingDiv) loadingDiv.style.display = 'none';
                const data = await response.json();

                if (!response.ok) {
                    if (data.login_required) {
                        alert("Session expired. Please log in again.");
                        window.location.href = '/';
                    }
                    throw new Error(data.error || `HTTP error! Status: ${response.status}`);
                }

                if (msgP && data.message) {
                    msgP.textContent = data.message;
                }

                if (data.recommendations && data.recommendations.length > 0) {
                    currentRecommendationIds = data.recommendations.map(song => song.id);
                    if (addAllButton) addAllButton.style.display = 'inline-block';
                    displaySongs(data.recommendations);
                } else {
                    recommendationsList.innerHTML = `<p>${data.message || 'No recommendations found for this mood.'}</p>`;
                }

            } catch (error) {
                console.error('Error fetching recommendations:', error);
                if (loadingDiv) loadingDiv.style.display = 'none';
                recommendationsList.innerHTML = `<p class="error-message">Failed to fetch recommendations. ${error.message}</p>`;
            }
        }
        
        function displaySongs(recommendations) {
             recommendationsList.innerHTML = ''; 
             recommendations.forEach(song => {
                const item = document.createElement('div');
                item.classList.add('recommendation-item');
                
                const albumArt = song.album_art || 'https://via.placeholder.com/100?text=No+Art';

                item.innerHTML = `
                    <a href="${song.url}" target="_blank" title="Listen on Spotify">
                        <img src="${albumArt}" alt="Album Art">
                    </a>
                    <div class="recommendation-details">
                        <h3>${song.name || 'Unknown Track'}</h3>
                        <p>${song.artist || 'Unknown Artist'}</p>
                        <p><span class="genre-badge">${song.super_genre}</span></p>
                    </div>
                `;
                
                recommendationsList.appendChild(item);
            });
        }
        
        async function handleAddAllToPlaylist() {
            const mood = document.getElementById('mood-display').textContent;
            if (!currentRecommendationIds || currentRecommendationIds.length === 0) {
                if (addAllStatus) addAllStatus.textContent = 'No songs to add.';
                return;
            }
            
            if (addAllButton) addAllButton.disabled = true;
            if (addAllStatus) addAllStatus.textContent = 'Adding all songs to playlist...';
            
            try {
                const response = await fetch('/add_all_to_playlist', {
                    method: 'POST',
                    headers: { 'Content-Type': 'application/json' },
                    body: JSON.stringify({ 
                        track_ids: currentRecommendationIds,
                        mood: mood
                    }),
                });
                const data = await response.json();
                if (response.ok && data.success) {
                    if (addAllStatus) addAllStatus.textContent = data.message;
                    if (addAllStatus) addAllStatus.className = 'status-message added-message';
                } else {
                    if (addAllStatus) addAllStatus.textContent = `Error: ${data.message || data.error}`;
                    if (addAllStatus) addAllStatus.className = 'status-message error-message-inline';
                    if (addAllButton) addAllButton.disabled = false;
                    if (data.login_required) { alert("Session expired."); window.location.href = '/'; }
                }
            } catch (error) {
                if (addAllStatus) addAllStatus.textContent = 'Network error.'; 
                if (addAllButton) addAllButton.disabled = false; 
            }
        }
        
        if (addAllButton) {
            addAllButton.addEventListener('click', handleAddAllToPlaylist);
        }
        
        fetchRecommendations();
    }
});