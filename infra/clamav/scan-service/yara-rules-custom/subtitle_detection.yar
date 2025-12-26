/*
    YARA Rule for detecting suspicious patterns in subtitle files
    Detects potential malicious content in .srt, .vtt, .ass, .sub files
    
    Author: Custom rule for media file scanning
    Date: 2025-12-26
*/

rule Suspicious_Subtitle_Content
{
    meta:
        description = "Detects suspicious patterns in subtitle files that may indicate malicious content"
        author = "Custom"
        date = "2025-12-26"
        reference = "https://github.com/Yara-Rules/rules"
    
    strings:
        // Suspicious script patterns in subtitles
        $script_tag1 = /<script/i
        $script_tag2 = /javascript:/i
        $script_tag3 = /onerror=/i
        $script_tag4 = /onload=/i
        
        // Suspicious URLs in subtitles
        $http_url = /https?:\/\/[^\s<>"]{10,50}/i
        $suspicious_domain = /[a-z0-9-]+\.(tk|ml|ga|cf|gq|top|xyz|click|download|stream)/i
        
        // Executable patterns (PE header in subtitle file)
        $pe_header = { 4D 5A }  // MZ header
        
        // Suspicious file extensions in subtitle content
        $exe_in_subtitle = /\.(exe|bat|cmd|ps1|vbs|js|jar|scr|com|pif)\s/i
        
        // Binary content in text file (null bytes)
        $null_bytes = { 00 00 }
        
    condition:
        // Match if file has subtitle extension and contains suspicious patterns
        (
            // Script injection attempts
            (2 of ($script_tag*)) or
            // Suspicious domains with URLs
            ($suspicious_domain and $http_url) or
            // Executable content (PE header)
            ($pe_header and filesize < 10485760) or  // PE header in file < 10MB
            // Executable file references
            ($exe_in_subtitle) or
            // Binary content in text file
            ($null_bytes and filesize < 1048576)  // Null bytes in file < 1MB
        )
}

rule Subtitle_File_Format
{
    meta:
        description = "Detects common subtitle file formats"
        author = "Custom"
        date = "2025-12-26"
    
    strings:
        // SRT format: sequence number, timestamp, text
        $srt_format = /\d+\s+\d{2}:\d{2}:\d{2}[,\.]\d{1,3}\s*-->\s*\d{2}:\d{2}:\d{2}[,\.]\d{1,3}/
        
        // VTT format: WEBVTT header
        $vtt_format = /WEBVTT/i
        
        // ASS/SSA format: [Script Info] or [V4+ Styles]
        $ass_format = /\[Script Info\]|\[V4\+ Styles\]|\[Events\]/i
        
        // SUB format: {start}{end}text
        $sub_format = /\{\d+\}\{\d+\}/
        
    condition:
        any of them
}

