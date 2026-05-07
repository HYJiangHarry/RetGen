import { useState } from "react"

const CONDITIONS = [
  "Normal fundus",
  "Diabetic retinopathy",
  "Age-related macular degeneration",
  "Glaucoma",
  "Retinal vein occlusion",
  "Pathological myopia",
  "Hypertensive retinopathy",
]

export default function App() {
  const [selected, setSelected] = useState(null)
  const [imageUrl, setImageUrl] = useState(null)
  const [generatedCondition, setGeneratedCondition] = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError] = useState(null)

  const handleGenerate = async () => {
    if (!selected) {
      setError("Please select a condition first.")
      return
    }

    setError(null)
    setIsLoading(true)
    setImageUrl(null)
    setGeneratedCondition(null)

    try {
      const res = await fetch("/api/generate", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ condition: selected }),
      })

      const data = await res.json()

      if (!res.ok || !data.success) {
        throw new Error(data.message || "Image generation failed. Please try again.")
      }

      setImageUrl(data.image_url)
      setGeneratedCondition(data.condition)
    } catch (err) {
      setError(err.message || "Image generation failed. Please try again.")
    } finally {
      setIsLoading(false)
    }
  }

  const renderRightPanel = () => {
    if (isLoading) {
      return (
        <div className="flex flex-col items-center justify-center h-full text-gray-400">
          <svg
            className="animate-spin h-12 w-12 text-blue-500 mb-4"
            xmlns="http://www.w3.org/2000/svg"
            fill="none"
            viewBox="0 0 24 24"
          >
            <circle
              className="opacity-25"
              cx="12"
              cy="12"
              r="10"
              stroke="currentColor"
              strokeWidth="4"
            />
            <path
              className="opacity-75"
              fill="currentColor"
              d="M4 12a8 8 0 018-8V0C5.373 0 0 5.373 0 12h4zm2 5.291A7.962 7.962 0 014 12H0c0 3.042 1.135 5.824 3 7.938l3-2.647z"
            />
          </svg>
          <p className="text-lg">Generating image...</p>
        </div>
      )
    }

    if (error) {
      return (
        <div className="flex flex-col items-center justify-center h-full text-red-400">
          <svg
            className="h-16 w-16 mb-4"
            fill="none"
            viewBox="0 0 24 24"
            stroke="currentColor"
            strokeWidth={1.5}
          >
            <path
              strokeLinecap="round"
              strokeLinejoin="round"
              d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126zM12 15.75h.007v.008H12v-.008z"
            />
          </svg>
          <p className="text-lg text-center">{error}</p>
        </div>
      )
    }

    if (imageUrl && generatedCondition) {
      return (
        <div className="flex flex-col items-center justify-center h-full">
          <img
            src={imageUrl}
            alt={generatedCondition}
            className="rounded-2xl shadow-2xl border border-gray-700 w-full max-w-md object-cover"
          />
          <p className="mt-4 text-lg font-semibold text-blue-400">
            {generatedCondition}
          </p>
        </div>
      )
    }

    return (
      <div className="flex flex-col items-center justify-center h-full text-gray-500">
        <svg
          className="h-20 w-20 mb-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          strokeWidth={1}
        >
          <path
            strokeLinecap="round"
            strokeLinejoin="round"
            d="M2.25 15.75l5.159-5.159a2.25 2.25 0 013.182 0l5.159 5.159m-1.5-1.5l1.409-1.41a2.25 2.25 0 013.182 0l2.909 2.91m-18 3.75h16.5a1.5 1.5 0 001.5-1.5V6a1.5 1.5 0 00-1.5-1.5H3.75A1.5 1.5 0 002.25 6v12a1.5 1.5 0 001.5 1.5zm10.5-11.25h.008v.008h-.008V8.25zm.375 0a.375.375 0 11-.75 0 .375.375 0 01.75 0z"
          />
        </svg>
        <p className="text-lg text-center">
          Please select a retinal condition and click Generate.
        </p>
      </div>
    )
  }

  return (
    <div className="flex flex-col md:flex-row h-screen bg-gray-950 text-white">
      {/* ---- Left Panel ---- */}
      <aside className="w-full md:w-80 lg:w-96 bg-gray-900 border-b md:border-b-0 md:border-r border-gray-800 flex flex-col p-6 shrink-0">
        <h1 className="text-xl font-bold mb-6 text-blue-400 leading-snug">
          Retinal Fundus<br />Image Generator
        </h1>

        <ul className="flex-1 space-y-1 overflow-y-auto">
          {CONDITIONS.map((cond) => (
            <li key={cond}>
              <button
                onClick={() => {
                  setSelected(cond)
                  setError(null)
                }}
                className={`w-full text-left px-4 py-3 rounded-lg text-sm font-medium transition-colors ${
                  selected === cond
                    ? "bg-blue-600/20 text-blue-400 border border-blue-500/40"
                    : "text-gray-400 hover:text-white hover:bg-gray-800 border border-transparent"
                }`}
              >
                {cond}
              </button>
            </li>
          ))}
        </ul>

        <button
          onClick={handleGenerate}
          disabled={isLoading}
          className={`mt-6 w-full py-3 rounded-xl font-semibold text-base transition-all ${
            isLoading
              ? "bg-gray-700 text-gray-500 cursor-not-allowed"
              : "bg-blue-600 hover:bg-blue-500 active:bg-blue-700 text-white shadow-lg shadow-blue-600/25"
          }`}
        >
          {isLoading ? "Generating..." : "Generate"}
        </button>
      </aside>

      {/* ---- Right Panel ---- */}
      <main className="flex-1 p-8 min-h-0">
        {renderRightPanel()}
      </main>
    </div>
  )
}
