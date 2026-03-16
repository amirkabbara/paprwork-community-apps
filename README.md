# Paprwork Community Apps

A curated collection of shareable app bundles for [Paprwork](https://github.com/Papr-ai/paprwork).

Browse and install these apps directly from the **Community Apps** tab inside Paprwork, or import them manually using the `import_app_bundle` tool.

---

## Available Apps

| App | Description | Tags |
|-----|-------------|------|
| **Hello World** | Minimal starter template for building your own apps | `template`, `starter` |
| **Expense Tracker** | Track daily expenses with category breakdowns and charts | `finance`, `charts`, `data` |

---

## Installing an App

### From Inside Paprwork (Recommended)

1. Open the **Apps** view
2. Switch to the **Community** tab
3. Browse available apps
4. Click **Import** on any app you want

### Via the AI Agent

Ask the agent:

> Import the expense tracker app from the community repo

The agent will use the `import_app_bundle` tool to clone and install it.

### Manual Import

```
import_app_bundle source:https://github.com/Papr-ai/paprwork-community-apps/bundles/expense-tracker
```

---

## Contributing

We welcome contributions! See [CONTRIBUTING.md](CONTRIBUTING.md) for guidelines on submitting your own app bundles.

---

## License

Individual bundles may have their own licenses. The registry and repository structure are licensed under [AGPL-3.0](https://www.gnu.org/licenses/agpl-3.0.html), matching the main Paprwork project.
