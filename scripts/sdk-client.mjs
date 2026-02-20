#!/usr/bin/env bun
/**
 * SDK Client wrapper - runs from project root for correct module resolution
 * Note: Using direct path because @opencode-ai/sdk package.json exports are broken
 * The package exports point to ./dist/index.js but files are in ./dist/src/index.js
 */
import { createOpencodeClient } from "../node_modules/@opencode-ai/sdk/dist/src/index.js"
import { join, dirname } from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = dirname(__filename)
const PROJECT_ROOT = join(__dirname, '..')

const DEFAULT_BASE_URL = "http://localhost:4096"

const readStdin = async () => {
  return await new Promise((resolve, reject) => {
    let data = ""
    process.stdin.setEncoding("utf8")
    process.stdin.on("data", (chunk) => { data += chunk })
    process.stdin.on("end", () => resolve(data))
    process.stdin.on("error", reject)
  })
}

const getQuery = (payload, defaultDir) => {
  const dir = payload?.directory || defaultDir
  if (!dir) return undefined
  return { directory: dir }
}

const main = async () => {
  const rawInput = await readStdin()
  const input = rawInput ? JSON.parse(rawInput) : {}
  const action = input.action
  const payload = input.payload ?? {}
  const baseUrl = input.baseUrl ?? DEFAULT_BASE_URL
  const directory = payload.directory || PROJECT_ROOT

  const client = createOpencodeClient({
    baseUrl,
    responseStyle: "data",
  })

  try {
    switch (action) {
      case "session_list": {
        const data = await client.session.list({ query: getQuery(payload, directory) })
        return { success: true, data }
      }
      case "session_get": {
        const data = await client.session.get({
          path: { id: payload.sessionId },
          query: getQuery(payload, directory),
        })
        return { success: true, data }
      }
      case "session_create": {
        const data = await client.session.create({
          body: { title: payload.title, parentID: payload.parentId },
          query: getQuery(payload, directory),
        })
        return { success: true, data }
      }
      case "session_delete": {
        const data = await client.session.delete({
          path: { id: payload.sessionId },
          query: getQuery(payload, directory),
        })
        return { success: true, data }
      }
      case "session_prompt": {
        const data = await client.session.prompt({
          path: { id: payload.sessionId },
          body: {
            agent: payload.agent,
            model: payload.model,
            noReply: payload.noReply,
            system: payload.system,
            tools: payload.tools,
            parts: payload.parts,
          },
          query: getQuery(payload, directory),
        })
        return { success: true, data }
      }
      case "agents_list": {
        const data = await client.app.agents()
        return { success: true, data }
      }
      default:
        return { success: false, error: `Unknown action: ${action}` }
    }
  } catch (error) {
    return { success: false, error: error?.message ?? String(error) }
  }
}

const result = await main()
process.stdout.write(JSON.stringify(result))
