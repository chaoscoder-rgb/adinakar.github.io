// blackjack.js - Modular browser-based Blackjack game

const suits = ['♠', '♥', '♦', '♣'];
const ranks = [
  {name: 'A', value: 11},
  {name: '2', value: 2},
  {name: '3', value: 3},
  {name: '4', value: 4},
  {name: '5', value: 5},
  {name: '6', value: 6},
  {name: '7', value: 7},
  {name: '8', value: 8},
  {name: '9', value: 9},
  {name: '10', value: 10},
  {name: 'J', value: 10},
  {name: 'Q', value: 10},
  {name: 'K', value: 10}
];

let deck, playerHand, dealerHand, splitHand, isSplit, activeHand, insuranceOffered, insuranceTaken, canDouble, canSplit;
let money = 300, bet = 10, totalWin = 0, totalLoss = 0;

const moneySpan = document.getElementById('money');
const totalWinSpan = document.getElementById('totalWin');
const totalLossSpan = document.getElementById('totalLoss');
const betInput = document.getElementById('bet');
const dealBtn = document.getElementById('dealBtn');
const hitBtn = document.getElementById('hitBtn');
const standBtn = document.getElementById('standBtn');
const doubleBtn = document.getElementById('doubleBtn');
const splitBtn = document.getElementById('splitBtn');
const insuranceBtn = document.getElementById('insuranceBtn');
const nextBtn = document.getElementById('nextBtn');
const messageDiv = document.getElementById('message');
const repeatBetBtn = document.getElementById('repeatBetBtn');
const currentBetLabel = document.getElementById('currentBetLabel');
const splitBetLabel = document.getElementById('splitBetLabel');
let lastBet = 10;

function shuffleDeck() {
  let d = [];
  for (let s of suits) for (let r of ranks) d.push({s, r: r.name, v: r.value});
  for (let i = d.length - 1; i > 0; i--) {
    let j = Math.floor(Math.random() * (i + 1));
    [d[i], d[j]] = [d[j], d[i]];
  }
  return d;
}

function handValue(hand) {
  let val = 0, aces = 0;
  for (let c of hand) {
    val += c.v;
    if (c.r === 'A') aces++;
  }
  while (val > 21 && aces) { val -= 10; aces--; }
  return val;
}

function handValueDisplay(hand) {
  let val = 0, aces = 0;
  for (let c of hand) {
    val += c.v;
    if (c.r === 'A') aces++;
  }
  let min = val, max = val;
  while (min > 21 && aces) { min -= 10; aces--; }
  if (min !== max && min !== val) return `${min} or ${val}`;
  if (aces && val <= 21) return `${val - 10} or ${val}`;
  return val;
}

function renderHand(hand, elem, hideFirst = false) {
  elem.innerHTML = '';
  hand.forEach((c, i) => {
    let cardDiv = document.createElement('div');
    cardDiv.className = 'card' + ((hideFirst && i === 0) ? ' back' : '');
    cardDiv.innerHTML = (hideFirst && i === 0) ? '' : `${c.r}${c.s}`;
    elem.appendChild(cardDiv);
  });
}

function updateUI() {
  moneySpan.textContent = `Money: $${money}`;
  totalWinSpan.textContent = `Total Won: $${totalWin}`;
  totalLossSpan.textContent = `Total Lost: $${totalLoss}`;
  betInput.max = Math.min(100, money);
  betInput.min = 1;
  betInput.value = Math.max(1, Math.min(bet, money));
  currentBetLabel.textContent = bet ? `(Bet: $${bet})` : '';
  splitBetLabel.textContent = isSplit ? `(Bet: $${bet})` : '';
}

function resetHands() {
  playerHand = [];
  dealerHand = [];
  splitHand = [];
  isSplit = false;
  activeHand = 'player';
  insuranceOffered = false;
  insuranceTaken = false;
  canDouble = true;
  canSplit = false;
  document.getElementById('splitHand').style.display = 'none';
}

function startHand(repeat = false) {
  resetHands();
  deck = shuffleDeck();
  if (repeat) bet = lastBet;
  else bet = parseInt(betInput.value);
  if (isNaN(bet) || bet < 1) bet = 1;
  if (bet > money) bet = money;
  lastBet = bet;
  money -= bet;
  updateUI();
  messageDiv.textContent = '';
  playerHand.push(deck.pop(), deck.pop());
  dealerHand.push(deck.pop(), deck.pop());
  renderHand(playerHand, document.getElementById('playerCards'));
  renderHand(dealerHand, document.getElementById('dealerCards'), true);
  document.getElementById('playerValue').textContent = `Value: ${handValueDisplay(playerHand)}`;
  document.getElementById('dealerValue').textContent = 'Value: ?';
  hitBtn.disabled = false;
  standBtn.disabled = false;
  doubleBtn.disabled = (money < bet) || false;
  splitBtn.disabled = !(playerHand[0].v === playerHand[1].v && money >= bet);
  insuranceBtn.disabled = dealerHand[1].r !== 'A';
  canSplit = !splitBtn.disabled;
  canDouble = !doubleBtn.disabled;
  nextBtn.style.display = 'none';
  betInput.disabled = true;
  dealBtn.disabled = true;
  repeatBetBtn.disabled = true;
  if (dealerHand[1].r === 'A') {
    insuranceOffered = true;
    insuranceBtn.disabled = false;
    messageDiv.textContent = 'Dealer shows Ace. Insurance?';
  }
}

function endHand(msg, win = 0, loss = 0) {
  renderHand(dealerHand, document.getElementById('dealerCards'));
  document.getElementById('dealerValue').textContent = `Value: ${handValueDisplay(dealerHand)}`;
  let emoji = '';
  if (win > loss) emoji = ' 😃👍';
  else if (loss > win) emoji = ' 😞👎';
  let amountMsg = '';
  if (win > loss) amountMsg = `Won $${win - loss}`;
  else if (loss > win) amountMsg = `Lost $${loss - win}`;
  else if (win === loss && win !== 0) amountMsg = 'Push!';
  messageDiv.textContent = `${msg}${amountMsg ? ' - ' + amountMsg : ''}${emoji}`;
  money += win;
  totalWin += win;
  totalLoss += loss;
  updateUI();
  hitBtn.disabled = true;
  standBtn.disabled = true;
  doubleBtn.disabled = true;
  splitBtn.disabled = true;
  insuranceBtn.disabled = true;
  nextBtn.style.display = '';
  betInput.disabled = false;
  dealBtn.disabled = false;
  repeatBetBtn.disabled = false;
}

function dealerPlay() {
  while (handValue(dealerHand) < 17) dealerHand.push(deck.pop());
}

function checkBlackjack() {
  if (handValue(playerHand) === 21 && playerHand.length === 2) {
    dealerPlay();
    if (handValue(dealerHand) === 21 && dealerHand.length === 2) {
      endHand('Push! Both have Blackjack.', bet, 0);
    } else {
      endHand('Blackjack! You win 1.5x bet.', Math.floor(bet * 2.5), 0);
    }
    return true;
  }
  return false;
}

function checkDealerBlackjack() {
  if (handValue(dealerHand) === 21 && dealerHand.length === 2) {
    renderHand(dealerHand, document.getElementById('dealerCards'));
    document.getElementById('dealerValue').textContent = `Value: ${handValue(dealerHand)}`;
    if (insuranceTaken) {
      endHand('Dealer has Blackjack. Insurance pays 2:1.', bet, 0);
    } else {
      endHand('Dealer has Blackjack. You lose.', 0, bet);
    }
    return true;
  }
  return false;
}

function playerBust(hand = playerHand) {
  if (handValue(hand) > 21) {
    if (isSplit && activeHand === 'player') {
      messageDiv.textContent = 'First hand busts! Now playing split hand.';
      activeHand = 'split';
      renderSplitHand();
    } else {
      endHand('Bust! You lose.', 0, bet);
    }
    return true;
  }
  return false;
}

function renderSplitHand() {
  document.getElementById('splitHand').style.display = '';
  renderHand(splitHand, document.getElementById('splitCards'));
  document.getElementById('splitValue').textContent = `Value: ${handValueDisplay(splitHand)}`;
  renderHand(playerHand, document.getElementById('playerCards'));
  document.getElementById('playerValue').textContent = `Value: ${handValueDisplay(playerHand)}`;
  hitBtn.disabled = false;
  standBtn.disabled = false;
  doubleBtn.disabled = (money < bet) || false;
  splitBtn.disabled = true;
  insuranceBtn.disabled = true;
}

function resolveHand(hand, betAmt) {
  dealerPlay();
  let playerVal = handValue(hand);
  let dealerVal = handValue(dealerHand);
  if (playerVal > 21) return {msg: 'Bust! You lose.', win: 0, loss: betAmt};
  if (dealerVal > 21) return {msg: 'Dealer busts! You win.', win: betAmt * 2, loss: 0};
  if (playerVal > dealerVal) return {msg: 'You win!', win: betAmt * 2, loss: 0};
  if (playerVal < dealerVal) return {msg: 'You lose.', win: 0, loss: betAmt};
  return {msg: 'Push!', win: betAmt, loss: 0};
}

// Event Listeners

dealBtn.onclick = () => {
  if (money < 1) {
    messageDiv.textContent = 'Out of money! Refresh to restart.';
    return;
  }
  startHand();
  if (!checkBlackjack() && !checkDealerBlackjack()) {
    // Continue playing
  }
};
repeatBetBtn.onclick = () => {
  if (money < lastBet) {
    messageDiv.textContent = 'Not enough money for previous bet.';
    return;
  }
  startHand(true);
  if (!checkBlackjack() && !checkDealerBlackjack()) {
    // Continue playing
  }
};

hitBtn.onclick = () => {
  if (isSplit && activeHand === 'split') {
    splitHand.push(deck.pop());
    renderSplitHand();
    if (playerBust(splitHand)) return;
  } else {
    playerHand.push(deck.pop());
    renderHand(playerHand, document.getElementById('playerCards'));
    document.getElementById('playerValue').textContent = `Value: ${handValue(playerHand)}`;
    if (playerBust()) return;
  }
};

standBtn.onclick = () => {
  if (isSplit && activeHand === 'player') {
    activeHand = 'split';
    messageDiv.textContent = 'Now playing split hand.';
    renderSplitHand();
    return;
  }
  let results = [];
  if (isSplit) {
    results.push(resolveHand(playerHand, bet));
    results.push(resolveHand(splitHand, bet));
    let msg = `First hand: ${results[0].msg} Second hand: ${results[1].msg}`;
    let win = results[0].win + results[1].win;
    let loss = results[0].loss + results[1].loss;
    endHand(msg, win, loss);
  } else {
    let result = resolveHand(playerHand, bet);
    endHand(result.msg, result.win, result.loss);
  }
};

doubleBtn.onclick = () => {
  if (money < bet) return;
  money -= bet;
  updateUI();
  if (isSplit && activeHand === 'split') {
    splitHand.push(deck.pop());
    renderSplitHand();
    let result = resolveHand(splitHand, bet * 2);
    endHand(result.msg, result.win, result.loss);
  } else {
    playerHand.push(deck.pop());
    renderHand(playerHand, document.getElementById('playerCards'));
    document.getElementById('playerValue').textContent = `Value: ${handValue(playerHand)}`;
    let result = resolveHand(playerHand, bet * 2);
    endHand(result.msg, result.win, result.loss);
  }
};

splitBtn.onclick = () => {
  if (money < bet) return;
  money -= bet;
  updateUI();
  isSplit = true;
  splitHand = [playerHand.pop()];
  playerHand.push(deck.pop());
  splitHand.push(deck.pop());
  activeHand = 'player';
  renderSplitHand();
};

insuranceBtn.onclick = () => {
  if (!insuranceOffered || money < Math.floor(bet / 2)) return;
  insuranceTaken = true;
  money -= Math.floor(bet / 2);
  updateUI();
  insuranceBtn.disabled = true;
  messageDiv.textContent = 'Insurance taken.';
};

nextBtn.onclick = () => {
  messageDiv.textContent = '';
  hitBtn.disabled = true;
  standBtn.disabled = true;
  doubleBtn.disabled = true;
  splitBtn.disabled = true;
  insuranceBtn.disabled = true;
  nextBtn.style.display = 'none';
  betInput.disabled = false;
  dealBtn.disabled = false;
  document.getElementById('playerCards').innerHTML = '';
  document.getElementById('dealerCards').innerHTML = '';
  document.getElementById('splitCards').innerHTML = '';
  document.getElementById('playerValue').textContent = '';
  document.getElementById('dealerValue').textContent = '';
  document.getElementById('splitValue').textContent = '';
  document.getElementById('splitHand').style.display = 'none';
};

betInput.oninput = () => {
  let v = parseInt(betInput.value);
  if (isNaN(v) || v < 1) v = 1;
  if (v > money) v = money;
  if (v > 100) v = 100;
  betInput.value = v;
};

updateUI();
nextBtn.style.display = 'none';
