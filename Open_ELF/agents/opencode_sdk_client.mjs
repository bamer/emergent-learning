import { createOpencodeClient } from "@opencode-ai/sdk"

const DEFAULT_BASE_URL = "http://localhost:4096"

const readStdin = async () => {
  return await new Promise((resolve, reject) => {
    let data = ""
    process.stdin.setEncoding("utf8")
    process.stdin.on("data", (chunk) => {
      data += chunk
    })
    process.stdin.on("end", () => resolve(data))
    process.stdin.on("error", reject)
  })
}

const getQuery = (payload) => {
  if (!payload?.directory) {
    return undefined
  }
  return { directory: payload.directory }
}

const main = async () => {
  const rawInput = await readStdin()
  const input = rawInput ? JSON.parse(rawInput) : {}
  const action = input.action
  const payload = input.payload ?? {}
  const baseUrl = input.baseUrl ?? DEFAULT_BASE_URL

  const client = createOpencodeClient({
    baseUrl,
    responseStyle: "data",
  })

  try {
    switch (action) {
      case "session_list": {
        const data = await client.session.list({ query: getQuery(payload) })
        return { success: true, data }
      }
      case "session_get": {
        const data = await client.session.get({
          path: { id: payload.sessionId },
          query: getQuery(payload),
        })
        return { success: true, data }
      }
      case "session_create": {
        const data = await client.session.create({
          body: { title: payload.title, parentID: payload.parentId },
          query: getQuery(payload),
        })
        return { success: true, data }
      }
      case "session_delete": {
        const data = await client.session.delete({
          path: { id: payload.sessionId },
          query: getQuery(payload),
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
          query: getQuery(payload),
        })
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
