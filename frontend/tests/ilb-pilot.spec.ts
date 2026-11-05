import { expect, test } from "@playwright/test";

test.use({ timezoneId: "America/Bahia" });

test("ILB real inventory supports search, attribution and the official redirect", async ({ page, context, request }, testInfo) => {
  test.skip(process.env.ILB_PILOT_BROWSER !== "1", "Opt-in: use the isolated ILB pilot, never acceptance fixtures.");
  const errors: string[] = [];
  page.on("pageerror", (error) => errors.push(error.message));
  const response = await request.get("/api/properties/?transaction_type=sale&ordering=-updated_at");
  expect(response.ok()).toBe(true);
  const inventory = await response.json();
  expect(inventory.count, "Wait for at least one successful partial ILB SyncRun").toBeGreaterThan(0);
  const property = inventory.results[0];
  const filters = new URLSearchParams({ city: property.city, state: property.state, transaction_type: "sale" });
  const detailResponse = await request.get(`/api/properties/${property.id}/?${filters}`);
  expect(detailResponse.ok()).toBe(true);
  const detail = await detailResponse.json();
  expect(detail.analytics_receipt).toBeNull(); // internal traffic stays excluded
  expect(detail.listings.length).toBeGreaterThan(0);
  for (const offer of detail.listings) {
    expect(offer.is_demo).toBe(false);
    expect(offer.source_url).toBe("https://www.imoveisleilaobrasil.com.br/api");
    expect(offer.attribution_text).toContain("CAIXA");
    expect(offer.source_inventory_date).toMatch(/^\d{4}-\d{2}-\d{2}$/);
    if (process.env.ILB_PILOT_PRICE_HISTORY === "1") {
      expect(offer.price_history.length).toBeGreaterThan(0);
    } else {
      expect(offer.price_history).toEqual([]);
    }
    expect(offer.description).toBe("");
    expect(["minimum", "reference", "asking"]).toContain(offer.price_kind);
    expect(offer.url).toMatch(/^https:\/\/venda-imoveis\.caixa\.gov\.br\/sistema\/detalhe-imovel\.asp\?hdnimovel=\d{5,20}$/);
  }
  await page.goto(`/?${filters}&property=${property.id}`);
  const dialog = page.getByRole("dialog");
  await expect(dialog.getByRole("heading", { name: "Comparar ofertas" })).toBeVisible();
  await expect(dialog.getByText(/Dados públicos da CAIXA via Imóveis Leilão Brasil/).first()).toBeVisible();
  await expect(dialog.getByText(/Lista de origem:/).first()).toBeVisible();
  const inventoryDate = new Intl.DateTimeFormat("pt-BR", { timeZone: "UTC" }).format(new Date(detail.listings[0].source_inventory_date));
  await expect(dialog.getByRole("row", { name: /Inventário da fonte/ }).first()).toContainText(inventoryDate);
  if (process.env.ILB_PILOT_PRICE_HISTORY === "1") {
    await expect(dialog.getByText("Histórico de preços", { exact: true }).first()).toBeVisible();
  } else {
    await expect(dialog.getByText("Histórico de preços", { exact: true })).toHaveCount(0);
  }
  const link = dialog.getByRole("link", { name: /Ver anúncio original/ }).first();
  const out = await link.getAttribute("href");
  const listingId = Number(out!.match(/^\/out\/(\d+)\//)![1]);
  const offer = detail.listings.find((item: { id: number }) => item.id === listingId);
  expect(offer).toBeDefined();
  let destination = "";
  await context.route("**/out/**", async (route) => {
    const result = await route.fetch({ maxRedirects: 0 });
    expect(result.status()).toBe(302);
    destination = result.headers().location;
    expect(destination).toBe(offer.url);
    await route.fulfill({ status: 200, contentType: "text/html", body: "Official redirect verified without external navigation" });
  });
  await link.scrollIntoViewIfNeeded();
  await page.screenshot({ path: testInfo.outputPath("ilb-real-offer.png") });
  const opened = page.waitForEvent("popup");
  await link.click();
  const popup = await opened;
  await expect(popup.getByText("Official redirect verified without external navigation")).toBeVisible();
  expect(destination).toBe(offer.url);
  expect(errors).toEqual([]);
  await popup.close();
});
