import http from 'k6/http';
import { check, sleep } from 'k6';

const BASE_URL = __ENV.BASE_URL || 'http://localhost:8080';
const SCENARIO = __ENV.SCENARIO || 'storm';

const scenarioOptions = {
  storm: {
    stages: [
      { duration: '10s', target: 1000 },
      { duration: '30s', target: 1000 },
      { duration: '30s', target: 0 },
    ],
  },
  wave: {
    stages: [
      { duration: '2m', target: 500 },
      { duration: '1m', target: 500 },
      { duration: '30s', target: 0 },
    ],
  },
  read_heavy: {
    stages: [
      { duration: '30s', target: 250 },
      { duration: '1m', target: 250 },
      { duration: '30s', target: 0 },
    ],
  },
  smoke: {
    vus: 1,
    iterations: 5,
  },
};

export const options = {
  ...(scenarioOptions[SCENARIO] || scenarioOptions.storm),
  thresholds: {
    http_req_failed: ['rate<0.05'],
    http_req_duration: ['p(95)<1000'],
  },
};

function randomInt(min, max) {
  return Math.floor(Math.random() * (max - min + 1)) + min;
}

function postJson(path, body) {
  return http.post(`${BASE_URL}${path}`, JSON.stringify(body), {
    headers: { 'Content-Type': 'application/json' },
  });
}

export function setup() {
  const suffix = `${Date.now()}-${Math.floor(Math.random() * 100000)}`;
  const users = [];
  [
    { name: 'Load Alice', email: `load-alice-${suffix}@example.com` },
    { name: 'Load Bob', email: `load-bob-${suffix}@example.com` },
  ].forEach((user) => {
    for (let attempt = 1; attempt <= 20; attempt += 1) {
      const res = postJson('/api/users', user);
      if (res.status === 200 || res.status === 201) {
        users.push(res.json('id'));
        return;
      }
      sleep(1);
    }
  });

  if (users.length === 0) {
    throw new Error('failed to seed test users before load test');
  }

  return { users };
}

export default function(data) {
  const users = data.users.length > 0 ? data.users : [1, 2];
  const writeProbability = SCENARIO === 'read_heavy' ? 0.3 : 0.8;

  if (Math.random() < writeProbability) {
    const payload = {
      user_id: users[randomInt(0, users.length - 1)],
      amount: Number((Math.random() * 100).toFixed(2)),
      description: `${SCENARIO} k6 load`,
    };
    const res = postJson('/api/orders', payload);
    check(res, { 'order created': (r) => r.status === 200 || r.status === 201 });
  } else {
    const res = http.get(`${BASE_URL}/api/orders`);
    check(res, { 'orders listed': (r) => r.status === 200 });
  }

  sleep(SCENARIO === 'storm' ? 0.05 : 0.1);
}
