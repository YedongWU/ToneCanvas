const puppeteer = require('puppeteer');
const fetch = require('node-fetch');

jest.mock('node-fetch', () => jest.fn());

beforeEach(() => {
  fetch.mockClear();
});

fetch.mockImplementation((url, options) => {
  if (url.includes('get-wav-file')) {
    return Promise.resolve({
      blob: () => Promise.resolve(new Blob(['mock audio data'], { type: 'audio/wav' })),
    });
  }
  if (url.includes('switch-wav-file')) {
    return Promise.resolve({
      json: () => Promise.resolve({ currentIndex: Math.floor(Math.random() * 10) }),
    });
  }
  return Promise.reject(new Error('Unknown API call'));
});

describe('Front-End Application', () => {
  let browser;
  let page;

  beforeAll(async () => {
    browser = await puppeteer.launch({
      headless: true,
      args: ['--no-sandbox', '--disable-setuid-sandbox'],
    });
    page = await browser.newPage();
    await page.goto('http://localhost:8080'); // 你需要运行本地服务器来提供前端页面
  });

  afterAll(async () => {
    await browser.close();
  });

  test('Canvas is rendered', async () => {
    const canvas = await page.$('#canvas');
    expect(canvas).not.toBeNull();
  });

  test('Green button click plays audio', async () => {
    await page.evaluate(() => {
      window.isAudioPlaying = false; // 确保初始状态
      window.dispatchEvent(new MouseEvent('mousedown', { clientX: 20, clientY: 20 }));
    });

    await new Promise(resolve => setTimeout(resolve, 100)); // 等待一段时间以确保事件处理完成

    const isAudioPlaying = await page.evaluate(() => window.isAudioPlaying);
    expect(isAudioPlaying).toBe(true);
  });

  test('Cyan button click switches audio', async () => {
    await page.evaluate(() => {
      window.currentAudioIndex = 0; // 确保初始状态
      window.dispatchEvent(new MouseEvent('mousedown', { clientX: 20, clientY: window.innerHeight - 20 }));
    });

    await new Promise(resolve => setTimeout(resolve, 100)); // 等待一段时间以确保事件处理完成

    const initialIndex = await page.evaluate(() => window.currentAudioIndex);

    await page.evaluate(() => {
      window.dispatchEvent(new MouseEvent('mousedown', { clientX: 20, clientY: window.innerHeight - 20 }));
    });

    await new Promise(resolve => setTimeout(resolve, 100)); // 等待一段时间以确保事件处理完成

    const newIndex = await page.evaluate(() => window.currentAudioIndex);
    expect(newIndex).not.toBe(initialIndex);
  });

  // 你可以根据需要添加更多测试用例
});
