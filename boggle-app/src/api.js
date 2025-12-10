// src/__mocks__/axios.js
const mockAxios = {
  create: jest.fn(() => mockAxios), // allow axios.create({...})
  get: jest.fn(() => Promise.resolve({ data: {} })),
  post: jest.fn(() => Promise.resolve({ data: {} })),
  put: jest.fn(() => Promise.resolve({ data: {} })),
  patch: jest.fn(() => Promise.resolve({ data: {} })),
  delete: jest.fn(() => Promise.resolve({ data: {} })),
  defaults: { headers: { common: {} } },
};

export default mockAxios;
