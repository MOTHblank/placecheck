import { expect, test } from "@playwright/test";
import { execFileSync } from "node:child_process";

function report(source: number, start: string) {
  const args = ["compose", "-p", process.env.ANALYTICS_COMPOSE_PROJECT || "placecheck-acceptance",
    "-f", "../docker-compose.yml", "-f", "../docker-compose.acceptance.yml"];
  if (process.env.ANALYTICS_COMPOSE_OVERRIDE) args.push("-f", process.env.ANALYTICS_COMPOSE_OVERRIDE);
  args.push("exec", "-T", "backend", "python", "manage.py", "journey_report", "--source", String(source), "--start", start);
  return JSON.parse(execFileSync("docker", args, { encoding: "utf8", timeout: 15000 }));
}

test("visible exposures, retransmission and repeated clicks yield 50% CTR", async ({ page, context, request }, testInfo) => {
  if (testInfo.project.name === "mobile") await page.setViewportSize({ width: 320, height: 851 });
  const city = `Metricópolis ${testInfo.project.name}`;
  const results = await (await request.get(`/api/properties/?city=${encodeURIComponent(city)}`)).json();
  expect(results.count, "Run prepare_analytics_fixtures in the isolated acceptance stack first").toBe(1);
  const property = results.results[0];
  const detail = await (await request.get(`/api/properties/${property.id}/?transaction_type=sale`)).json();
  expect(detail.listings).toHaveLength(3);
  const source = detail.listings[0].source_id;
  const start = new Date().toISOString();
  const accepted: { event_id: string; kind: string; [key: string]: unknown }[] = [];
  page.on("response", async (response) => {
    if (!response.url().endsWith("/api/analytics/events/") || response.request().method() !== "POST") return;
    if (response.status() === 201) accepted.push(response.request().postDataJSON());
  });
  await page.goto(`/`);
  await page.getByPlaceholder("Cidade, bairro ou região").fill(city);
  await page.getByRole("button", { name: "Buscar imóveis", exact: true }).click();
  await expect(page.getByText("1 imóveis encontrados", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: /Ver ofertas/ }).click();
  const dialog = page.getByRole("dialog");
  const articles = dialog.locator(".offer-item");
  await expect(articles).toHaveCount(3);
  const prices = dialog.getByRole("region", { name: "Tabela: Preços anunciados", exact: true });
  // These offers are visible in the table before either detailed card is visible.
  await expect.poll(() => accepted.filter((event) => event.kind === "exposure").length).toBe(testInfo.project.name === "desktop" ? 2 : 1);
  await prices.locator("thead th").nth(2).scrollIntoViewIfNeeded();
  await expect.poll(() => accepted.filter((event) => event.kind === "exposure").length).toBe(2);
  const exposure = accepted.find((event) => event.kind === "exposure")!;
  const retransmission = await request.post("/api/analytics/events/", { data: exposure });
  expect(retransmission.status()).toBe(200);
  await context.route("**/out/**", async (route) => {
    const upstream = await route.fetch({ maxRedirects: 0 });
    expect(upstream.status()).toBe(302);
    expect(upstream.headers().location).toMatch(/^https:\/\/fixture\.invalid\/analytics\//);
    await route.fulfill({ status: 200, contentType: "text/html", body: "External navigation intercepted" });
  });
  const link = articles.first().getByRole("link", { name: /Ver anúncio original/ });
  await link.scrollIntoViewIfNeeded();
  await expect(link).toHaveAttribute("href", /exposure=/);
  for (let index = 0; index < 3; index++) {
    const popupReady = page.waitForEvent("popup");
    await link.click();
    const popup = await popupReady;
    await expect(popup.getByText("External navigation intercepted")).toBeVisible();
    await popup.close();
  }
  const row = report(source, start).sources[0];
  expect(row.exposures).toBe(2); // table and card share an exposure; the third offer stayed hidden
  expect(row.exposures_with_redirect).toBe(1);
  expect(row.raw_redirects).toBe(3);
  expect(row.ctr_percent).toBe(50);
  await page.screenshot({ path: testInfo.outputPath("analytics.png") });
});

test("explicit repeated searches count while ordering pagination and history do not", async ({ page }) => {
  let searches = 0;
  page.on("response", (response) => {
    if (response.url().endsWith("/api/analytics/events/") && response.status() === 201 && response.request().postDataJSON()?.kind === "search") searches++;
  });
  await page.goto("/");
  await expect(page.getByRole("button", { name: /Ver ofertas/ }).first()).toBeVisible();
  expect(searches).toBe(0);
  await page.getByPlaceholder("Cidade, bairro ou região").fill("Testópolis");
  const submit = page.getByRole("button", { name: "Buscar imóveis", exact: true });
  await submit.click();
  await expect.poll(() => searches).toBe(1);
  await submit.click();
  await expect.poll(() => searches).toBe(2);
  await page.getByLabel("Ordenar resultados").selectOption("price");
  await expect(page.getByText("14 imóveis encontrados", { exact: true })).toBeVisible();
  await page.getByRole("button", { name: "Próxima", exact: true }).click();
  await expect(page.getByText("Página 2 de 2")).toBeVisible();
  await page.goBack();
  await expect(page.getByText("Página 1 de 2")).toBeVisible();
  expect(searches).toBe(2);
  await page.reload();
  await expect.poll(() => searches).toBe(3);
});

test("failed instrumentation preserves the usable original link", async ({ page, request }, testInfo) => {
  await page.route("**/api/analytics/events/", (route) => route.fulfill({ status: 503, body: "unavailable" }));
  await page.goto(`/?location=${encodeURIComponent(`Metricópolis ${testInfo.project.name}`)}`);
  await page.getByRole("button", { name: /Ver ofertas/ }).click();
  const link = page.getByRole("dialog").getByRole("link", { name: /Ver anúncio original/ }).first();
  await expect(link).toHaveAttribute("href", /^\/out\/\d+\/$/);
  const response = await request.get((await link.getAttribute("href"))!, { maxRedirects: 0 });
  expect(response.status()).toBe(302);
});
