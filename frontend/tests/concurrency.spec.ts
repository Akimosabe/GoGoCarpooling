import { expect, test, type Browser, type BrowserContext, type Page } from '@playwright/test'

const BASE_URL = 'http://localhost:5173'
const USER_1 = {
  email: 'akimosabe@yandex.ru',
  password: '3101Akim!',
}
const USER_2 = {
  email: 'akimo7abe@gmail.com',
  password: '3101Akim!',
}
const SEARCH_URL_STATIC =
  '/search?origin_id=1080&origin=%D0%9C%D0%BE%D1%81%D0%BA%D0%B2%D0%B0%2C+%D0%9C%D0%BE%D1%81%D0%BA%D0%B2%D0%B0&destination_id=664&destination=%D0%A1%D0%B0%D0%BD%D0%BA%D1%82-%D0%9F%D0%B5%D1%82%D0%B5%D1%80%D0%B1%D1%83%D1%80%D0%B3%2C+%D0%A1%D0%B0%D0%BD%D0%BA%D1%82-%D0%9F%D0%B5%D1%82%D0%B5%D1%80%D0%B1%D1%83%D1%80%D0%B3&date=2026-03-30&page=1'

async function newCtx(browser: Browser): Promise<BrowserContext> {
  return browser.newContext({ baseURL: BASE_URL })
}

async function login(page: Page, email: string, password: string): Promise<void> {
  await page.goto('/auth')
  const form = page.locator('form').first()
  await form.locator('input[type="email"]').fill(email)
  await form.locator('input[type="password"]').first().fill(password)
  await Promise.all([
    page.waitForURL((url) => !url.pathname.startsWith('/auth'), { timeout: 20_000 }),
    form.locator('button[type="submit"]').click(),
  ])
}

async function ensureSearchPageLoaded(page: Page, pathWithQuery: string): Promise<void> {
  await page.goto(pathWithQuery)
  await expect(page).toHaveURL(new RegExp(`${BASE_URL}/search`))
  await page.waitForLoadState('networkidle')
  await expect(page.locator('h1').first()).toBeVisible()
}

async function ensureBookedOneSeat(page: Page, tripId: number): Promise<void> {
  await page.goto(`/trips/${tripId}`)
  await page.waitForLoadState('networkidle')

  const seatInput = page.locator('input[type="number"][aria-label]').first()
  if (await seatInput.count()) {
    await seatInput.fill('1')
    const bookButton = seatInput.locator('xpath=following::button[1]')
    const bookResponse = page.waitForResponse((res) => {
      return res.request().method() === 'POST' && res.url().includes(`/api/trips/${tripId}/book/`)
    })
    await bookButton.click()
    const response = await bookResponse
    if (!response.ok()) {
      throw new Error(`Не удалось забронировать место: статус ${response.status()}`)
    }
    return
  }

  const bookingsResponse = await page.request.get('/api/my-bookings/?page=1')
  if (!bookingsResponse.ok()) {
    throw new Error(`Не удалось получить мои бронирования. Статус: ${bookingsResponse.status()}`)
  }
  const bookingsJson = (await bookingsResponse.json()) as {
    results?: Array<{ id: number; seats_count: number; status: string; trip: { id: number } }>
  }
  const existing = (bookingsJson.results ?? []).find(
    (b) => b.trip?.id === tripId && (b.status === 'confirmed' || b.status === 'pending')
  )

  if (existing && existing.seats_count === 1) {
    return
  }

  if (existing) {
    const cancelResponse = await page.request.post(`/api/bookings/${existing.id}/cancel/`)
    if (!cancelResponse.ok()) {
      throw new Error(`Не удалось отменить существующее бронирование. Статус: ${cancelResponse.status()}`)
    }
  }

  const createResponse = await page.request.post(`/api/trips/${tripId}/book/`, {
    data: { seats_count: 1, comment: '' },
  })
  if (!createResponse.ok()) {
    throw new Error(`Не удалось создать бронирование. Статус: ${createResponse.status()}`)
  }
}

async function openNotifications(page: Page): Promise<void> {
  await page.goto('/')
  const notificationsButton = page.locator('header button[aria-label]').first()
  await notificationsButton.click()
  await expect(page.locator('header .absolute.right-0.top-full').first()).toBeVisible()
}

async function editProfileNameAddM(page: Page): Promise<void> {
  await page.goto('/profile')
  await page.waitForLoadState('networkidle')

  const editButtonNearName = page.locator('h1 + button[aria-label]').first()
  if (await editButtonNearName.count()) {
    await editButtonNearName.click()
  } else {
    await page.locator('button[aria-label]').first().click()
  }

  const nameInput = page.locator('input[type="text"]').first()
  await expect(nameInput).toBeVisible()
  const current = await nameInput.inputValue()
  const next = current.endsWith('м') ? current : `${current}м`
  await nameInput.fill(next)

  await page.locator('.space-y-3 .flex.gap-2 button').first().click()
  await expect(nameInput).toBeHidden()
}

async function selectCityInput(input: ReturnType<Page['locator']>, query: string, cityRegex: RegExp): Promise<void> {
  await input.fill(query)
  const listbox = input.page().locator('ul[role="listbox"]').last()
  await expect(listbox).toBeVisible({ timeout: 10_000 })
  const preferred = listbox.locator('li[role="option"]').filter({ hasText: cityRegex }).first()
  if (await preferred.count()) {
    await preferred.click()
    return
  }
  await listbox.locator('li[role="option"]').first().click()
}

async function publishTripMoscowSpbToday2300(page: Page): Promise<void> {
  await page.goto('/trips/create')
  const form = page.locator('form').first()
  await expect(form).toBeVisible()

  const routeInputs = form.locator('input[type="text"]').nth(0)
  const destinationInput = form.locator('input[type="text"]').nth(1)
  await selectCityInput(routeInputs, 'Москва', /Москва/i)
  await selectCityInput(destinationInput, 'Санкт', /Санкт|Петербург/i)

  await form.locator('input[type="time"]').fill('23:00')
  await form.locator('input[placeholder="500"]').fill('4000')

  const submit = form.locator('button[type="submit"]')
  await Promise.all([
    page.waitForURL(new RegExp(`${BASE_URL}/trips/\\d+`), { timeout: 20_000 }),
    submit.click(),
  ])
}

test.describe('Требования одновременности 1.4.2.3', () => {
  test('Параллельное выполнение поиска поездок и бронирования', async ({ browser }) => {
    const ctxBooking = await newCtx(browser)
    const ctxSearch = await newCtx(browser)
    const bookingPage = await ctxBooking.newPage()
    const searchPage = await ctxSearch.newPage()

    await Promise.all([
      (async () => {
        await login(bookingPage, USER_1.email, USER_1.password)
        await ensureBookedOneSeat(bookingPage, 33) // ПОКА НЕ ПРИДУМАЛ КАК МЕНЯТЬ АВТОМАТОМ, ТУТ ТАК-ТО НЕЛЬЗЯ ОДИН РАЗ БРОНИРОВАТЬСЯ В ОДНУ И ТУ ЖЕ
      })(),
      ensureSearchPageLoaded(searchPage, SEARCH_URL_STATIC),
    ])

    await Promise.all([ctxBooking.close(), ctxSearch.close()])
  })

  test('Управление профилем и обработка уведомлений', async ({ browser }) => {
    const ctxProfile = await newCtx(browser)
    const ctxNotifications = await newCtx(browser)
    const profilePage = await ctxProfile.newPage()
    const notificationsPage = await ctxNotifications.newPage()

    await Promise.all([
      (async () => {
        await login(profilePage, USER_2.email, USER_2.password)
        await editProfileNameAddM(profilePage)
      })(),
      (async () => {
        await login(notificationsPage, USER_1.email, USER_1.password)
        await openNotifications(notificationsPage)
      })(),
    ])

    await Promise.all([ctxProfile.close(), ctxNotifications.close()])
  })

  test('Публикация поездок и просмотр результатов поиска', async ({ browser }) => {
    const ctxPublish = await newCtx(browser)
    const ctxSearch = await newCtx(browser)
    const publishPage = await ctxPublish.newPage()
    const searchPage = await ctxSearch.newPage()

    const today = new Date().toISOString().slice(0, 10)
    const searchToday =
      `/search?origin_id=1080&origin=%D0%9C%D0%BE%D1%81%D0%BA%D0%B2%D0%B0%2C+%D0%9C%D0%BE%D1%81%D0%BA%D0%B2%D0%B0` +
      `&destination_id=664&destination=%D0%A1%D0%B0%D0%BD%D0%BA%D1%82-%D0%9F%D0%B5%D1%82%D0%B5%D1%80%D0%B1%D1%83%D1%80%D0%B3%2C+%D0%A1%D0%B0%D0%BD%D0%BA%D1%82-%D0%9F%D0%B5%D1%82%D0%B5%D1%80%D0%B1%D1%83%D1%80%D0%B3` +
      `&date=${today}&page=1`

    await Promise.all([
      (async () => {
        await login(publishPage, USER_2.email, USER_2.password)
        await publishTripMoscowSpbToday2300(publishPage)
      })(),
      ensureSearchPageLoaded(searchPage, searchToday),
    ])

    await Promise.all([ctxPublish.close(), ctxSearch.close()])
  })
})
