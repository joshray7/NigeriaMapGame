// game.js - per-state 60s timer + immediate next-state behavior
let guessedStates = JSON.parse(localStorage.getItem("guessedStates")) || [];



// CONFIG
const PER_STATE_SECONDS = 60;   // 60 seconds per guess
const ATTEMPTS_PER_STATE = 3;   // how many tries per state before it's failed
const MAX_REVEAL_USES = 2;
const MAX_SKIP_USES = 2;
const stateDescriptions = {
  Abia: "Known as God’s Own State, Abia is famous for its commercial hub Aba, renowned for leather works and craftsmanship.",
  Adamawa: "Located in northeastern Nigeria, Adamawa is home to the Sukur Cultural Landscape, a UNESCO World Heritage Site.",
  AkwaIbom: "Rich in oil and culture, Akwa Ibom is known for its cuisine and the beautiful city of Uyo.",
  Anambra: "Known as the Light of the Nation, Anambra is famous for Onitsha Market and historical sites like Ogbunike Caves.",
  Bauchi: "Home to Yankari National Park, Bauchi is a top tourist destination known for wildlife and warm springs.",
  Bayelsa: "Located in the Niger Delta, Bayelsa is rich in crude oil and known for being the home state of former President Goodluck Jonathan.",
  Benue: "Known as the Food Basket of the Nation, Benue produces large quantities of yams, oranges, and grains.",
  Borno: "The Home of Peace, Borno is Nigeria’s largest state by area and home to the historic Kanem-Bornu Empire.",
  CrossRiver: "Known for its tropical forests, Obudu Mountain Resort, and the Calabar Carnival — Africa’s biggest street party.",
  Delta: "A rich oil-producing state in the Niger Delta, Delta is known for its diverse ethnic groups and natural resources.",
  Ebonyi: "Nicknamed the Salt of the Nation, Ebonyi is famous for its large salt lakes and rice production.",
  Edo: "Home of the ancient Benin Kingdom, Edo is known for its bronze art, culture, and heritage.",
  Ekiti: "Known as the Fountain of Knowledge, Ekiti State has a high literacy rate and beautiful rolling hills.",
  Enugu: "The Coal City State, Enugu was a major coal mining center and is now a hub of culture and education.",
  Gombe: "The Jewel in the Savannah, Gombe is known for its natural beauty and friendly people.",
  Imo: "Nicknamed the Eastern Heartland, Imo is known for Owerri city, hospitality, and cultural festivals.",
  Jigawa: "Located in the northwest, Jigawa is known for agriculture and traditional Hausa culture.",
  Kaduna: "Known as the Center of Learning, Kaduna hosts many educational institutions and a rich cultural heritage.",
  Kano: "One of the oldest cities in West Africa, Kano is a major trade and industrial hub with deep Islamic history.",
  Katsina: "Home to the historic Gobarau Minaret and the Emir’s Palace, Katsina is rich in northern tradition.",
  Kebbi: "Known for Argungu Fishing Festival, Kebbi is an agricultural hub and cultural center of the northwest.",
  Kogi: "Nicknamed the Confluence State, Kogi is where the River Niger and River Benue meet.",
  Kwara: "Known as the State of Harmony, Kwara blends Yoruba and northern cultures beautifully.",
  Lagos: "Nigeria’s economic powerhouse, Lagos is famous for its beaches, nightlife, and status as Africa’s largest city.",
  Nasarawa: "Known as the Home of Solid Minerals, Nasarawa is rich in natural resources and scenic beauty.",
  Niger: "Nigeria’s largest state by landmass, Niger hosts Kainji Dam and the Gurara Waterfalls.",
  Ogun: "The Gateway State, Ogun is home to industries, Olumo Rock, and Nigeria’s first university (UI in Ibadan was built near Ogun).",
  Ondo: "Known as the Sunshine State, Ondo is rich in cocoa and blessed with scenic landscapes.",
  Osun: "Home to the Osun-Osogbo Sacred Grove, a UNESCO World Heritage Site, and rich Yoruba traditions.",
  Oyo: "Known as the Pacesetter State, Oyo was the seat of the ancient Oyo Empire and home to Ibadan, one of Nigeria’s largest cities.",
  Plateau: "Nicknamed the Home of Peace and Tourism, Plateau has a cool climate and beautiful rock formations.",
  Rivers: "Known for oil wealth and the Port Harcourt city, Rivers is a key industrial and cultural center.",
  Sokoto: "The Seat of the Caliphate, Sokoto is an Islamic cultural center with deep historical significance.",
  Taraba: "Nicknamed Nature’s Gift to the Nation, Taraba is home to Mambilla Plateau and diverse ethnic groups.",
  Yobe: "Located in the northeast, Yobe is known for livestock farming and ancient Kanuri traditions.",
  Zamfara: "Known for its gold deposits and agriculture, Zamfara is rich in culture and history.",
  FCT: "Abuja, the Federal Capital Territory, is Nigeria’s capital city — planned, modern, and home to Aso Rock and the National Mosque."
};


// STATE
let allStates = [];
let remainingStates = [];
let currentState = null;        // DOM element (path)
let attemptsLeft = ATTEMPTS_PER_STATE;
let correctCount = 0;
let perStateTimer = null;
let perStateTimeLeft = PER_STATE_SECONDS;
let gameRunning = false;
let totalStates = 36
let revealUses = 0;
let skipUses = 0;



// ELEMENTS
let startBtn, skipBtn, revealBtn, submitBtn, restartBtn, guessInput, timerEl, scoreEl, messageEl, svgRoot;

function normalizeName(name) {
  return (name || "").toString().trim().toLowerCase().replace(/\s+/g, "").replace(/state/g, "").replace(/-/g, "");
}

function getStateNameFromElement(el) {
  if (!el) return "";
  // prefer <title> content if present
  const title = el.querySelector && el.querySelector("title");
  if (title && title.textContent && title.textContent.trim().length > 0) return title.textContent.trim();
  // otherwise fallback to element id
  return el.id || "";
}

function updateScoreDisplay() {
  scoreEl.textContent = `Correct: ${correctCount}/ ${totalStates}`;
}

function updateTimerDisplay() {
  const m = Math.floor(perStateTimeLeft / 60).toString().padStart(2, "0");
  const s = (perStateTimeLeft % 60).toString().padStart(2, "0");
  timerEl.textContent = `Time left: ${m}:${s}`;
}

function startPerStateTimer() {
  clearInterval(perStateTimer);
  perStateTimeLeft = PER_STATE_SECONDS;
  updateTimerDisplay();
  perStateTimer = setInterval(() => {
    if (!gameRunning || !currentState) return;
    perStateTimeLeft--;
    updateTimerDisplay();
    if (perStateTimeLeft <= 0) {
      clearInterval(perStateTimer);
      handleStateTimeout();
    }
  }, 1000);
}

function stopPerStateTimer() {
  clearInterval(perStateTimer);
}

function resetAllStateColors() {
  allStates.forEach(p => p.style.fill = "#ccc");
}

const moreInfoBtn = document.getElementById("more-info-btn");


function showDescription(stateName) {
  const descriptionDiv = document.getElementById("description");
  const desc = stateDescriptions[stateName] || "No description available.";
  descriptionDiv.innerHTML = `<strong>${stateName}:</strong> ${desc}`;

  moreInfoBtn.style.display = "inline-block";
  moreInfoBtn.onclick = () => {
    pauseGame();
    window.location.href = `/state/${stateName}`;
  };

}

function pauseGame() {
  gameRunning = false;
  stopPerStateTimer();
}



// Show state name on map (centered in bbox)
function showStateNameOnMap(el, color = "black") {
  try {
    const svg = svgRoot;
    if (!svg || !el) return;
    const bbox = el.getBBox();
    const text = document.createElementNS("http://www.w3.org/2000/svg", "text");
    text.setAttribute("x", bbox.x + bbox.width / 2);
    text.setAttribute("y", bbox.y + bbox.height / 2 + 4); // small vertical nudge
    text.setAttribute("text-anchor", "middle");
    text.setAttribute("fill", color);
    text.setAttribute("font-weight", "700");
    text.setAttribute("font-size", "12");
    // add white stroke so text is visible on colored shapes
    text.setAttribute("style", "paint-order:stroke; stroke:white; stroke-width:1px;");
    text.textContent = getStateNameFromElement(el);
    svg.appendChild(text);
  } catch (err) {
    // some SVGs have problematic getBBox when element hidden — ignore if fails
    console.warn("showStateNameOnMap error:", err);
  }
}


  function pickRandomState() {
    // clear previous label/color
    if (!gameRunning) return;
    resetAllStateColors();
  
    const available = remainingStates.filter(s => s.dataset.guessed !== "true");
    if (available.length === 0) {
      // game finished
      messageEl.textContent = `🎉 You finished all states! YOU GOT : ${correctCount} / ${totalStates}`

      if (correctCount === totalStates){
        messageEl.textContent = `🎉 Congratulations! You Guessed all the states right 🏆 `
      }
      if (correctCount < 10){
        messageEl.textContent = ` ${correctCount}, Your score is very low 😔, try harder next time!!`
      }
      gameRunning = false;
      document.getElementById("restartBtn").style.display = "block";

      stopPerStateTimer();
      return;
    }

    currentState = available[Math.floor(Math.random() * available.length)];
    // color current state
    currentState.style.fill = "#28a745"; // green highlight for the active one
    attemptsLeft = ATTEMPTS_PER_STATE;
    messageEl.textContent = `🟢 A state is colored — you have ${attemptsLeft} tries and ${PER_STATE_SECONDS} seconds`;
    startPerStateTimer();
}
  

function handleStateTimeout() {
  // treat as failure for this state: reveal its name, mark guessed, move on
  if (!currentState) return;
  messageEl.textContent = `⏰ Time's up for ${getStateNameFromElement(currentState)} — moving to next`;
  // mark as revealed/guessed so it won't show again
  currentState.dataset.guessed = "true";
  // show name on map (orange to indicate revealed)
  currentState.style.fill = "#f39c12"; // orange
  showStateNameOnMap(currentState, "black");
  // small delay so user sees result
  setTimeout(() => {
    pickRandomState();
  }, 1000);
}

function submitGuessHandler() {
  if (!gameRunning || !currentState) return;

  const raw = (guessInput.value || "").trim();
  if (!raw) {
    messageEl.textContent = "✏️ Type a state name first.";
    return;
  }

  const guess = normalizeName(raw);
  const correct = normalizeName(getStateNameFromElement(currentState));

  if (guess === correct) {
    // correct
    stopPerStateTimer();
    correctCount++;
    const stateName = getStateNameFromElement(currentState);

    // ✅ Only push if not already stored
    if (!guessedStates.includes(stateName)) {
      guessedStates.push(stateName);
      localStorage.setItem("guessedStates", JSON.stringify(guessedStates));
    }
    currentState.dataset.guessed = "true";
    currentState.style.fill = "#2ecc71"; // lighter green to indicate success
    showStateNameOnMap(currentState, "black");
    updateScoreDisplay();
    messageEl.textContent = `✅ Correct! It was ${getStateNameFromElement(currentState)}. Next state coming...`;
    showDescription(getStateNameFromElement(currentState));
    guessedStates.push(getStateNameFromElement(currentState));
    guessInput.value = "";

    // short pause then next state
    setTimeout(() => {
      pickRandomState();
    }, 900);
    

  } else {
    // wrong
    attemptsLeft--;
    if (attemptsLeft > 0) {
      messageEl.textContent = `❌ Wrong! ${attemptsLeft} tries left for this state.`;
    } else {
      // user failed this state
      stopPerStateTimer();
      messageEl.textContent = `😢 No tries left. The correct answer was ${getStateNameFromElement(currentState)}. Moving on...`;
      currentState.dataset.guessed = "true";
      currentState.style.fill = "#e74c3c"; // red to indicate fail
      showStateNameOnMap(currentState, "black");
      guessInput.value = "";
      setTimeout(() => {
        pickRandomState();
      }, 900);
    }
  }
}

function skipHandler() {
  if (!gameRunning || !currentState) return;
  if (skipUses >= MAX_SKIP_USES) {
    messageEl.textContent = "🚫 You’ve used all your skips!";
    return;
  }

  skipUses++;

  stopPerStateTimer();
  messageEl.textContent = `⏭️ You've Skipped a state.`;
  currentState.style.fill = "#95a5a6"; // grey for skipped
  remainingStates.push(currentState);
  setTimeout(() => {
    pickRandomState();
  }, 700);
}

function revealHandler() {
  if (!gameRunning || !currentState) return;
  if (revealUses >= MAX_REVEAL_USES) {
    messageEl.textContent = "🚫 You’ve used all your reveals!";
    return;
  }
  revealUses++;
  stopPerStateTimer();
  messageEl.textContent = `👀 Revealed: ${getStateNameFromElement(currentState)}. Moving on...`;
  currentState.dataset.guessed = "true";
  currentState.style.fill = "#f39c12"; // orange
  showStateNameOnMap(currentState, "black");
  showDescription(getStateNameFromElement(currentState));

  setTimeout(() => {
    pickRandomState();
  }, 900);
}

function startGameHandler() {

  document.getElementById("game-rules").style.display = "none"; // hide rules
// initialize lists
svgRoot = document.getElementById("nigeria-map") || document.querySelector("svg");
if (!svgRoot) {
  alert("SVG map not found (id 'nigeria-map'). Make sure your SVG is inline and has that id.");
  return;
}

stopPerStateTimer(); // stop any running timer
let savedGuessedStates = JSON.parse(localStorage.getItem("guessedStates")) || [];

correctCount = savedGuessedStates.length;
skipUses = 0;
revealUses = 0;
currentState = null;
gameRunning = true;

// Remove all text labels (state names)
svgRoot.querySelectorAll("text").forEach(t => t.remove());

// Reset all state colors and guessed flags
allStates.forEach(p => {
  const stateName = getStateNameFromElement(p);
  if (guessedStates.includes(stateName)) {
    // ✅ Already guessed — keep green
    p.style.fill = "#2ecc71";
    p.dataset.guessed = "true";
    showStateNameOnMap(p, "black");
  } else {
    p.style.fill = "#ccc";
    p.dataset.guessed = "";
  }
});


// fetch all state paths (only direct path elements inside svg)
allStates = Array.from(svgRoot.querySelectorAll("path"));
// reset guessed flags
allStates.forEach(p => { p.dataset.guessed = ""; p.style.fill = "#ccc"; });

remainingStates = [...allStates];
correctCount = 0;
updateScoreDisplay();
gameRunning = true;
messageEl.textContent = "Game started! Good luck.";
pickRandomState();
}



// RULES TOGGLE FUNCTIONALITY
document.addEventListener("DOMContentLoaded", () => {
    const toggleBtn = document.getElementById("toggle-rules");
    const rulesBox = document.getElementById("game-rules");
  
    if (toggleBtn && rulesBox) {
      toggleBtn.addEventListener("click", () => {
        if (rulesBox.style.display === "none") {
          rulesBox.style.display = "block";
          toggleBtn.textContent = "❌ Hide Game Rules";
          toggleBtn.style.backgroundColor = "#dc3545"; // red when open
        } else {
          rulesBox.style.display = "none";
          toggleBtn.textContent = "📘 Show Game Rules";
          toggleBtn.style.backgroundColor = "#007bff"; // blue when closed
        }
      });
    }
  });

  

// Setup DOM references & listeners after DOM ready
document.addEventListener("DOMContentLoaded", () => {
  startBtn = document.getElementById("start-btn");
  skipBtn = document.getElementById("skip-btn");
  revealBtn = document.getElementById("reveal-btn");
  submitBtn = document.getElementById("submit-guess");
  guessInput = document.getElementById("guess-input");
  timerEl = document.getElementById("timer");
  scoreEl = document.getElementById("score");
  messageEl = document.getElementById("message");
  svgRoot = document.getElementById("nigeriaMap") || document.querySelector("svg");
  restartBtn = document.getElementById("restartBtn");
  

  if (!startBtn || !submitBtn || !skipBtn || !revealBtn) {
    console.warn("Missing one or more game control elements. Check IDs.");
  }

  startBtn.addEventListener("click", startGameHandler);
  submitBtn.addEventListener("click", submitGuessHandler);
  skipBtn.addEventListener("click", skipHandler);
  revealBtn.addEventListener("click", revealHandler);


  // allow Enter in guess input
  if (guessInput) {
    guessInput.addEventListener("keydown", (e) => {
      if (e.key === "Enter") {
        e.preventDefault();
        submitGuessHandler();
      }
    });
  }

  // initial display
  updateScoreDisplay();
  updateTimerDisplay();
});
