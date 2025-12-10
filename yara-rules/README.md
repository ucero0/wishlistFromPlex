# YARA Rules for Media Scanner

This directory contains YARA rules used by the virus scanner to detect malware patterns in downloaded files.

## Included Rules

- `malware_signatures.yar` - Basic malware detection patterns

## Adding More Rules

You can add additional YARA rules by:

1. Creating new `.yar` or `.yara` files in this directory
2. Downloading community rules from trusted sources:
   - [Yara-Rules Repository](https://github.com/Yara-Rules/rules)
   - [awesome-yara](https://github.com/InQuest/awesome-yara)

## Rule Format

```yara
rule RuleName {
    meta:
        description = "Description of what this rule detects"
        author = "Your name"
        severity = "low|medium|high|critical"
    
    strings:
        $string1 = "pattern to match"
        $hex1 = { 4D 5A }  // Hex pattern
        
    condition:
        any of them
}
```

## Testing Rules

Test your rules before deploying:

```bash
yara -r malware_signatures.yar /path/to/test/file
```

