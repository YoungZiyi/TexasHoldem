const http = require('http');
const fs = require('fs');
const path = require('path');
const WebSocket = require('ws');

const PORT = process.env.PORT || 4000;

// ============ 牌组工具 ============
const SUITS = ['♠', '♥', '♦', '♣'];
const RANKS = ['2','3','4','5','6','7','8','9','10','J','Q','K','A'];
const RANK_VALUES = { '2':2,'3':3,'4':4,'5':5,'6':6,'7':7,'8':8,'9':9,'10':10,'J':11,'Q':12,'K':13,'A':14 };

function createDeck() {
  const deck = [];
  for (const suit of SUITS) {
    for (const rank of RANKS) {
      deck.push({ suit, rank, value: RANK_VALUES[rank] });
    }
  }
  return deck;
}

function shuffle(deck) {
  for (let i = deck.length - 1; i > 0; i--) {
    const j = Math.floor(Math.random() * (i + 1));
    [deck[i], deck[j]] = [deck[j], deck[i]];
  }
  return deck;
}

function getCombinations(arr, k) {
  const result = [];
  function backtrack(start, current) {
    if (current.length === k) { result.push([...current]); return; }
    for (let i = start; i < arr.length; i++) {
      current.push(arr[i]);
      backtrack(i + 1, current);
      current.pop();
    }
  }
  backtrack(0, []);
  return result;
}

// 评估5张牌，返回 [牌型等级, 踢脚...]
function evaluate5(cards) {
  const values = cards.map(c => c.value).sort((a, b) => b - a);
  const suits = cards.map(c => c.suit);
  const isFlush = suits.every(s => s === suits[0]);

  let isStraight = false, straightHigh = 0;
  const uniq = [...new Set(values)].sort((a, b) => b - a);
  if (uniq.length === 5) {
    if (uniq[0] - uniq[4] === 4) { isStraight = true; straightHigh = uniq[0]; }
    if (uniq[0] === 14 && uniq[1] === 5 && uniq[4] === 2) { isStraight = true; straightHigh = 5; }
  }

  if (isFlush && isStraight) return [9, straightHigh];

  const counts = {};
  for (const v of values) counts[v] = (counts[v] || 0) + 1;
  const ce = Object.entries(counts).map(([v,c]) => [parseInt(v), c])
    .sort((a,b) => (b[1] !== a[1] ? b[1]-a[1] : b[0]-a[0]));

  if (ce[0][1] === 4) return [8, ce[0][0], ce[1][0]];
  if (ce[0][1] === 3 && ce[1][1] === 2) return [7, ce[0][0], ce[1][0]];
  if (isFlush) return [6, ...values];
  if (isStraight) return [5, straightHigh];
  if (ce[0][1] === 3) return [4, ce[0][0], ...ce.slice(1).map(e => e[0])];
  if (ce[0][1] === 2 && ce[1][1] === 2) return [3, ce[0][0], ce[1][0], ce[2][0]];
  if (ce[0][1] === 2) return [2, ce[0][0], ...ce.slice(1).map(e => e[0])];
  return [1, ...values];
}

function evaluate7(cards7) {
  let best = null;
  for (const combo of getCombinations(cards7, 5)) {
    const rank = evaluate5(combo);
    if (!best || compareRanks(rank, best) > 0) best = rank;
  }
  return best;
}

function compareRanks(a, b) {
  for (let i = 0; i < Math.max(a.length, b.length); i++) {
    const av = a[i] || 0, bv = b[i] || 0;
    if (av > bv) return 1;
    if (av < bv) return -1;
  }
  return 0;
}

// ============ 游戏状态 ============
const rooms = new Map();
const clients = new Map();

function genId() { return Math.random().toString(36).substring(2, 8).toUpperCase(); }
function broadcast(room, msg) {
  const data = JSON.stringify(msg);
  for (const p of room.players) {
    if (p.ws && p.ws.readyState === WebSocket.OPEN) p.ws.send(data);
  }
}
function send(ws, msg) { if (ws.readyState === WebSocket.OPEN) ws.send(JSON.stringify(msg)); }

function createRoom(ws, name) {
  const roomId = genId();
  const playerId = genId();
  const room = {
    id: roomId, players: [], status: 'waiting',
    deck: [], communityCards: [], pot: 0, street: null,
    currentPlayerIndex: -1, dealerIndex: -1,
    smallBlind: 10, bigBlind: 20, streetHighestBet: 0, minRaise: 20,
  };
  const host = { id: playerId, name, chips: 1000, hand: [], streetBet: 0, totalBet: 0,
    folded: false, allIn: false, hasActed: false, ws, isHost: true, seat: 0 };
  room.players.push(host);
  rooms.set(roomId, room);
  clients.set(ws, { playerId, roomId });
  send(ws, { type: 'joined', roomId, playerId, isHost: true });
  broadcastState(room);
  return room;
}

function joinRoom(ws, roomId, name) {
  roomId = roomId.toUpperCase();
  const room = rooms.get(roomId);
  if (!room) { send(ws, { type: 'error', message: '房间不存在' }); return; }

  // 重连：同名且断开
  const dc = room.players.find(p => p.name === name && !p.ws);
  if (dc) {
    dc.ws = ws;
    clients.set(ws, { playerId: dc.id, roomId });
    send(ws, { type: 'joined', roomId, playerId: dc.id, isHost: dc.isHost });
    broadcastState(room);
    return;
  }

  if (room.status !== 'waiting') { send(ws, { type: 'error', message: '游戏已开始，如之前断开请用相同名字重新加入' }); return; }
  if (room.players.length >= 9) { send(ws, { type: 'error', message: '房间已满' }); return; }

  const playerId = genId();
  const p = { id: playerId, name, chips: 1000, hand: [], streetBet: 0, totalBet: 0,
    folded: false, allIn: false, hasActed: false, ws, isHost: false, seat: room.players.length };
  room.players.push(p);
  clients.set(ws, { playerId, roomId });
  send(ws, { type: 'joined', roomId, playerId, isHost: false });
  broadcastState(room);
}

function leaveRoom(ws) {
  const c = clients.get(ws);
  if (!c) return;
  const { playerId, roomId } = c;
  const room = rooms.get(roomId);
  if (!room) return;
  const idx = room.players.findIndex(p => p.id === playerId);
  if (idx === -1) return;
  const p = room.players[idx];

  if (room.status === 'waiting') {
    room.players.splice(idx, 1);
    room.players.forEach((pl, i) => pl.seat = i);
    if (room.players.length === 0) rooms.delete(roomId);
    else broadcastState(room);
  } else {
    p.ws = null;
    p.folded = true;
    checkAdvance(room);
  }
  clients.delete(ws);
}

function broadcastState(room) {
  const pub = getPublicState(room);
  for (const p of room.players) {
    const ps = { ...pub, yourHand: p.hand, yourId: p.id,
      yourTurn: room.currentPlayerIndex >= 0 && room.players[room.currentPlayerIndex]?.id === p.id };
    if (p.ws && p.ws.readyState === WebSocket.OPEN) p.ws.send(JSON.stringify({ type: 'state', state: ps }));
  }
}

function getPublicState(room) {
  return {
    roomId: room.id, status: room.status,
    players: room.players.map(p => ({
      id: p.id, name: p.name, chips: p.chips, streetBet: p.streetBet,
      totalBet: p.totalBet, folded: p.folded, allIn: p.allIn,
      hasActed: p.hasActed, isHost: p.isHost, seat: p.seat,
      handCount: p.hand.length, connected: !!p.ws,
    })),
    communityCards: room.communityCards, pot: room.pot, street: room.street,
    currentPlayerIndex: room.currentPlayerIndex, dealerIndex: room.dealerIndex,
    smallBlind: room.smallBlind, bigBlind: room.bigBlind,
    streetHighestBet: room.streetHighestBet, minRaise: room.minRaise,
    playerCount: room.players.length,
  };
}

// ============ 游戏逻辑 ============
function startGame(room) {
  if (room.players.length < 2) return { error: '至少需要2名玩家' };
  room.status = 'playing';
  room.dealerIndex = 0;
  startNewHand(room);
}

function startNewHand(room) {
  const eligible = room.players.filter(p => p.chips > 0);
  if (eligible.length < 2) {
    room.status = 'waiting';
    broadcastState(room);
    return;
  }

  room.deck = shuffle(createDeck());
  room.communityCards = [];
  room.pot = 0;
  room.street = 'preflop';
  room.streetHighestBet = 0;
  room.minRaise = room.bigBlind;

  for (const p of room.players) {
    if (p.chips <= 0) {
      p.hand = []; p.streetBet = 0; p.totalBet = 0;
      p.folded = true; p.allIn = false; p.hasActed = true;
    } else {
      p.hand = [room.deck.pop(), room.deck.pop()];
      p.streetBet = 0; p.totalBet = 0;
      p.folded = false; p.allIn = false; p.hasActed = false;
    }
  }

  let sbIdx, bbIdx;
  if (room.players.length === 2) {
    sbIdx = room.dealerIndex;
    bbIdx = (room.dealerIndex + 1) % 2;
  } else {
    sbIdx = (room.dealerIndex + 1) % room.players.length;
    bbIdx = (room.dealerIndex + 2) % room.players.length;
  }

  placeBet(room.players[sbIdx], room.smallBlind, room);
  placeBet(room.players[bbIdx], room.bigBlind, room);
  room.streetHighestBet = room.bigBlind;

  room.currentPlayerIndex = (bbIdx + 1) % room.players.length;
  skipInactive(room);
  broadcastState(room);
}

function placeBet(p, amt, room) {
  const actual = Math.min(amt, p.chips);
  p.chips -= actual;
  p.streetBet += actual;
  p.totalBet += actual;
  room.pot += actual;
  if (p.chips === 0) p.allIn = true;
}

function skipInactive(room) {
  let attempts = 0;
  while (attempts < room.players.length) {
    const p = room.players[room.currentPlayerIndex];
    if (!p.folded && !p.allIn && p.ws) break;
    room.currentPlayerIndex = (room.currentPlayerIndex + 1) % room.players.length;
    attempts++;
  }
}

function handleAction(room, playerId, action) {
  if (room.status !== 'playing') return;
  const cur = room.players[room.currentPlayerIndex];
  if (!cur || cur.id !== playerId) return;
  const { type, amount } = action;

  switch (type) {
    case 'fold': {
      cur.folded = true; cur.hasActed = true; break;
    }
    case 'check': {
      if (cur.streetBet < room.streetHighestBet) {
        send(cur.ws, { type: 'error', message: '需要跟注或加注' }); return;
      }
      cur.hasActed = true; break;
    }
    case 'call': {
      const callAmt = room.streetHighestBet - cur.streetBet;
      if (callAmt <= 0) { cur.hasActed = true; break; }
      placeBet(cur, callAmt, room);
      cur.hasActed = true; break;
    }
    case 'raise': {
      const raiseTo = amount;
      if (raiseTo <= room.streetHighestBet) {
        send(cur.ws, { type: 'error', message: '加注额必须高于当前最高下注' }); return;
      }
      if (raiseTo < room.streetHighestBet + room.minRaise) {
        send(cur.ws, { type: 'error', message: `最小加注到 ${room.streetHighestBet + room.minRaise}` }); return;
      }
      const addAmt = raiseTo - cur.streetBet;
      if (addAmt > cur.chips) { send(cur.ws, { type: 'error', message: '筹码不足' }); return; }
      for (const p of room.players) {
        if (!p.folded && !p.allIn && p.id !== cur.id) p.hasActed = false;
      }
      placeBet(cur, addAmt, room);
      room.streetHighestBet = raiseTo;
      room.minRaise = raiseTo - (room.streetHighestBet - addAmt);
      cur.hasActed = true; break;
    }
    case 'allin': {
      const addAmt = cur.chips;
      if (addAmt <= 0) { cur.hasActed = true; break; }
      const newTotal = cur.streetBet + addAmt;
      if (newTotal > room.streetHighestBet) {
        for (const p of room.players) {
          if (!p.folded && !p.allIn && p.id !== cur.id) p.hasActed = false;
        }
        room.streetHighestBet = newTotal;
        room.minRaise = Math.max(room.minRaise, addAmt);
      }
      placeBet(cur, addAmt, room);
      cur.hasActed = true; break;
    }
  }
  checkAdvance(room);
}

function checkAdvance(room) {
  const active = room.players.filter(p => !p.folded);
  if (active.length === 1) {
    endHand(room, active, '其他玩家弃牌');
    return;
  }

  const nonAllIn = active.filter(p => !p.allIn);
  const needAction = nonAllIn.filter(p => !p.hasActed);
  const allMatched = nonAllIn.every(p => p.streetBet === room.streetHighestBet);

  if (needAction.length === 0 && allMatched) {
    endStreet(room);
    return;
  }

  let nextIdx = room.currentPlayerIndex, found = false;
  for (let i = 0; i < room.players.length; i++) {
    nextIdx = (nextIdx + 1) % room.players.length;
    const p = room.players[nextIdx];
    if (!p.folded && !p.allIn && p.ws) { found = true; break; }
  }
  if (!found) { endStreet(room); return; }

  room.currentPlayerIndex = nextIdx;
  broadcastState(room);
}

function endStreet(room) {
  for (const p of room.players) { p.streetBet = 0; p.hasActed = false; }
  room.streetHighestBet = 0;
  room.minRaise = room.bigBlind;

  const streets = ['preflop', 'flop', 'turn', 'river'];
  const idx = streets.indexOf(room.street);

  if (room.street === 'preflop') {
    room.communityCards.push(room.deck.pop(), room.deck.pop(), room.deck.pop());
    room.street = 'flop';
  } else if (room.street === 'flop') {
    room.communityCards.push(room.deck.pop());
    room.street = 'turn';
  } else if (room.street === 'turn') {
    room.communityCards.push(room.deck.pop());
    room.street = 'river';
  } else if (room.street === 'river') {
    showdown(room); return;
  }

  room.currentPlayerIndex = (room.dealerIndex + 1) % room.players.length;
  skipInactive(room);
  broadcastState(room);
}

function showdown(room) {
  room.status = 'showdown';
  const active = room.players.filter(p => !p.folded);
  const sorted = [...room.players].sort((a, b) => a.totalBet - b.totalBet);
  let prevBet = 0;
  const pots = [];

  for (let i = 0; i < sorted.length; i++) {
    const diff = sorted[i].totalBet - prevBet;
    if (diff > 0) {
      const size = diff * (sorted.length - i);
      const eligible = sorted.slice(i).filter(p => !p.folded).map(p => p.id);
      if (eligible.length > 0) pots.push({ size, eligible });
      prevBet = sorted[i].totalBet;
    }
  }

  const allWinners = new Set();
  for (const pot of pots) {
    let best = null, winners = [];
    for (const p of active) {
      if (!pot.eligible.includes(p.id)) continue;
      const rank = evaluate7([...p.hand, ...room.communityCards]);
      if (!best || compareRanks(rank, best) > 0) { best = rank; winners = [p]; }
      else if (compareRanks(rank, best) === 0) winners.push(p);
    }
    const share = Math.floor(pot.size / winners.length);
    const rem = pot.size % winners.length;
    for (let i = 0; i < winners.length; i++) {
      winners[i].chips += share + (i < rem ? 1 : 0);
      allWinners.add(winners[i].id);
    }
  }

  broadcast(room, {
    type: 'showdown',
    winners: Array.from(allWinners),
    hands: active.map(p => ({ playerId: p.id, hand: p.hand })),
    communityCards: room.communityCards,
  });
  broadcastState(room);
  setTimeout(() => prepareNextHand(room), 6000);
}

function endHand(room, winners, reason) {
  const share = Math.floor(room.pot / winners.length);
  const rem = room.pot % winners.length;
  for (let i = 0; i < winners.length; i++) winners[i].chips += share + (i < rem ? 1 : 0);

  room.status = 'showdown';
  broadcast(room, {
    type: 'showdown',
    winners: winners.map(w => w.id),
    reason,
    hands: room.players.filter(p => !p.folded).map(p => ({ playerId: p.id, hand: p.hand })),
    communityCards: room.communityCards,
  });
  broadcastState(room);
  setTimeout(() => prepareNextHand(room), 6000);
}

function prepareNextHand(room) {
  if (room.players.length < 2) { room.status = 'waiting'; broadcastState(room); return; }
  room.dealerIndex = (room.dealerIndex + 1) % room.players.length;
  room.players = room.players.filter(p => p.chips > 0 || p.ws);
  if (room.players.length < 2) { room.status = 'waiting'; broadcastState(room); return; }
  room.players.forEach((p, i) => p.seat = i);
  room.status = 'playing';
  startNewHand(room);
}

// ============ WebSocket ============
const wss = new WebSocket.Server({ noServer: true });

wss.on('connection', (ws) => {
  ws.on('message', (data) => {
    try {
      const msg = JSON.parse(data);
      const c = clients.get(ws);

      if (msg.type === 'create_room') {
        createRoom(ws, msg.name);
      } else if (msg.type === 'join_room') {
        joinRoom(ws, msg.roomId, msg.name);
      } else if (msg.type === 'start_game') {
        if (!c) return;
        const room = rooms.get(c.roomId);
        if (!room) return;
        const p = room.players.find(pl => pl.id === c.playerId);
        if (!p?.isHost) return;
        const r = startGame(room);
        if (r?.error) send(ws, { type: 'error', message: r.error });
      } else if (msg.type === 'action') {
        if (!c) return;
        const room = rooms.get(c.roomId);
        if (!room) return;
        handleAction(room, c.playerId, msg.action);
      } else if (msg.type === 'rebuy') {
        if (!c) return;
        const room = rooms.get(c.roomId);
        if (!room) return;
        const p = room.players.find(pl => pl.id === c.playerId);
        if (p) { p.chips = 1000; broadcastState(room); }
      }
    } catch (e) { console.error('msg err', e); }
  });
  ws.on('close', () => leaveRoom(ws));
  ws.on('error', () => leaveRoom(ws));
});

// ============ HTTP ============
const server = http.createServer((req, res) => {
  if (req.url === '/' || req.url === '/index.html') {
    fs.readFile(path.join(__dirname, 'public', 'index.html'), (err, data) => {
      if (err) { res.writeHead(500); res.end('Error'); }
      else { res.writeHead(200, { 'Content-Type': 'text/html' }); res.end(data); }
    });
  } else {
    res.writeHead(404); res.end('Not Found');
  }
});

server.on('upgrade', (req, socket, head) => {
  wss.handleUpgrade(req, socket, head, (ws) => wss.emit('connection', ws, req));
});

server.listen(PORT, () => {
  console.log(`Texas Poker Server running on http://0.0.0.0:${PORT}`);
});
