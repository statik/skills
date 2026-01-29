# OpenCode Configuration

## Skill Permissions

OpenCode uses pattern-based permissions to control skill access. Configure in `opencode.json`:

```json
{
  "permission": {
    "skill": {
      "dns-troubleshooter": "allow",
      "*": "ask"
    }
  }
}
```

### Permission Values

| Value | Description |
|-------|-------------|
| `"allow"` | Skill can be used without prompting |
| `"deny"` | Skill is disabled |
| `"ask"` | Prompt user before using skill |

### Agent-Specific Configuration

Override skill access for specific agents:

```json
{
  "agents": {
    "plan": {
      "skills": ["dns-troubleshooter"]
    },
    "build": {
      "skills": []
    }
  }
}
```

## More Information

See the [OpenCode Skills Documentation](https://opencode.ai/docs/skills) for more details.
