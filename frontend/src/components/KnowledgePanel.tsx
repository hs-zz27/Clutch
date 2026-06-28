import { useRef, useState } from 'react'
import { useMutation, useQuery, useQueryClient } from '@tanstack/react-query'
import { BookOpen, FileText, Search, Upload, X } from 'lucide-react'
import { ClutchApi, ApiError } from '../api'
import { Button, EmptyState, ErrorNote, Modal, Panel, Spinner } from './ui'
import { MarkdownLite } from './MarkdownLite'
import { formatDateTime } from '../lib/format'
import type { KnowledgeDocument, KnowledgeSearchResponse } from '../types'

const MAX_UPLOAD_BYTES = 10 * 1024 * 1024 // 10 MB - keep in sync with the backend
const ALLOWED_EXTENSIONS = [
  '.pdf', '.txt', '.md', '.markdown', '.csv', '.tsv',
  '.json', '.doc', '.docx', '.rtf', '.pptx', '.xlsx', '.log',
]

function formatBytes(n: number | null): string {
  if (!n) return ''
  if (n < 1024) return `${n} B`
  if (n < 1024 * 1024) return `${(n / 1024).toFixed(1)} KB`
  return `${(n / (1024 * 1024)).toFixed(1)} MB`
}

export function KnowledgePanel() {
  const qc = useQueryClient()
  const fileRef = useRef<HTMLInputElement>(null)
  const [query, setQuery] = useState('')
  const [answer, setAnswer] = useState<KnowledgeSearchResponse | null>(null)
  const [validationError, setValidationError] = useState<string | null>(null)

  const docs = useQuery({ queryKey: ['documents'], queryFn: ClutchApi.listDocuments })

  const upload = useMutation({
    mutationFn: (file: File) => ClutchApi.uploadDocument(file),
    onSuccess: () => {
      if (fileRef.current) fileRef.current.value = ''
      qc.invalidateQueries({ queryKey: ['documents'] })
    },
  })
  const search = useMutation({
    mutationFn: () => ClutchApi.searchKnowledge(query.trim()),
    onSuccess: setAnswer,
  })

  const [pendingDelete, setPendingDelete] = useState<KnowledgeDocument | null>(null)
  const remove = useMutation({
    mutationFn: (id: number) => ClutchApi.deleteDocument(id),
    onSuccess: () => {
      setPendingDelete(null)
      qc.invalidateQueries({ queryKey: ['documents'] })
    },
  })

  function handlePicked(file: File | undefined) {
    setValidationError(null)
    if (fileRef.current) fileRef.current.value = '' // allow re-picking the same file
    if (!file) return
    const dot = file.name.lastIndexOf('.')
    const ext = dot >= 0 ? file.name.slice(dot).toLowerCase() : ''
    if (!ALLOWED_EXTENSIONS.includes(ext)) {
      setValidationError(`Unsupported file type "${ext || 'unknown'}". Allowed: PDF, TXT, MD, CSV, JSON, DOC(X), RTF, PPTX, XLSX.`)
      return
    }
    if (file.size > MAX_UPLOAD_BYTES) {
      setValidationError(`That file is ${formatBytes(file.size)} - the limit is 10 MB. Upload a smaller document.`)
      return
    }
    upload.mutate(file)
  }

  const uploadError =
    validationError ??
    (upload.isError ? ((upload.error as ApiError)?.detail ?? 'Upload failed.') : null)

  return (
    <Panel
      title="Knowledge base"
      icon={<BookOpen className="h-4 w-4 text-ember" />}
      rail="teal"
      actions={
        <>
          <input
            ref={fileRef}
            type="file"
            accept={ALLOWED_EXTENSIONS.join(',')}
            className="hidden"
            onChange={(e) => handlePicked(e.target.files?.[0])}
          />
          <Button variant="ghost" loading={upload.isPending} onClick={() => fileRef.current?.click()}>
            <Upload className="h-4 w-4" /> Upload
          </Button>
        </>
      }
    >
      {uploadError && <div className="mb-3"><ErrorNote>{uploadError}</ErrorNote></div>}

      <div className="mb-3 text-[11px] text-faint">
        Max 10 MB · PDF, TXT, MD, CSV, JSON, DOC(X), RTF, PPTX, XLSX
      </div>

      <div className="mb-4 space-y-2 rounded-lg border border-line-soft bg-ink-2 p-3">
        <div className="flex gap-2">
          <input
            className="field py-1.5"
            placeholder="Ask your documents… (grounded RAG)"
            value={query}
            onChange={(e) => setQuery(e.target.value)}
            onKeyDown={(e) => e.key === 'Enter' && query.trim() && search.mutate()}
          />
          <Button variant="ember" loading={search.isPending} disabled={!query.trim()} onClick={() => search.mutate()}>
            <Search className="h-4 w-4" />
          </Button>
        </div>
        {search.isError && <ErrorNote>{(search.error as ApiError)?.detail ?? 'Search failed.'}</ErrorNote>}
        {answer && (
          <div className="rounded-lg border border-teal/30 bg-teal/5 px-3 py-2">
            <MarkdownLite text={answer.answer} />
            {answer.citations.length > 0 && (
              <div className="mt-2 flex flex-wrap gap-1.5">
                {answer.citations.map((c, i) => (
                  <span key={i} className="chip border-teal/40 text-teal">{c}</span>
                ))}
              </div>
            )}
          </div>
        )}
      </div>

      {docs.isLoading ? (
        <div className="flex justify-center py-4"><Spinner /></div>
      ) : docs.isError ? (
        <ErrorNote>Could not load documents.</ErrorNote>
      ) : (docs.data?.length ?? 0) === 0 ? (
        <EmptyState icon={<FileText className="h-6 w-6" />} title="No documents yet" hint="Upload briefs, rubrics or specs to ground the agent." />
      ) : (
        <ul className="space-y-1.5">
          {docs.data!.map((d) => (
            <li key={d.id} className="flex items-center justify-between gap-2 rounded-lg border border-line-soft bg-ink-2 px-3 py-2">
              <span className="flex min-w-0 items-center gap-2">
                <FileText className="h-4 w-4 shrink-0 text-faint" />
                <span className="truncate text-sm">{d.filename}</span>
              </span>
              <span className="flex shrink-0 items-center gap-2">
                <span className="font-mono text-[11px] text-faint">{formatBytes(d.size_bytes)} · {formatDateTime(d.uploaded_at)}</span>
                <button
                  type="button"
                  className="rounded p-1 text-faint transition-colors hover:text-coral"
                  aria-label={`Remove ${d.filename}`}
                  onClick={() => setPendingDelete(d)}
                >
                  <X className="h-4 w-4" />
                </button>
              </span>
            </li>
          ))}
        </ul>
      )}

      <Modal
        open={pendingDelete !== null}
        onClose={() => {
          if (!remove.isPending) setPendingDelete(null)
        }}
        title="Remove from knowledge base?"
      >
        <div className="space-y-4">
          <p className="text-sm text-muted">
            Would you like to remove{' '}
            <span className="font-600 text-paper">{pendingDelete?.filename}</span>{' '}
            from your knowledge base? This deletes its indexed content, so it will
            no longer be used to answer questions. This can’t be undone.
          </p>
          {remove.isError && (
            <ErrorNote>{(remove.error as ApiError)?.detail ?? 'Could not remove the file.'}</ErrorNote>
          )}
          <div className="flex justify-end gap-2">
            <Button variant="ghost" disabled={remove.isPending} onClick={() => setPendingDelete(null)}>
              Cancel
            </Button>
            <Button
              variant="ember"
              loading={remove.isPending}
              onClick={() => pendingDelete && remove.mutate(pendingDelete.id)}
            >
              <X className="h-4 w-4" /> Remove
            </Button>
          </div>
        </div>
      </Modal>
    </Panel>
  )
}
