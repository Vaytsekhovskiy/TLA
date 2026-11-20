$ErrorActionPreference = 'Stop'
try {
    $word = [Runtime.InteropServices.Marshal]::GetActiveObject('Word.Application')
    foreach ($document in $word.Documents) {
        if ($document.FullName -eq 'C:\projects\tla\experiment\REPORT.docx') {
            [pscustomobject]@{
                Path = $document.FullName
                Saved = $document.Saved
                ReadOnly = $document.ReadOnly
            } | Format-List
        }
    }
} catch {
    Write-Output $_.Exception.Message
}
