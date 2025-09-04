import { useState, useRef } from "react";
import { cn } from "../lib/utils";
import { Upload, Camera, X, Loader2, Image as ImageIcon } from "lucide-react";

interface VisualQAResult {
  answer: string;
  confidence: number;
  extracted_text: string;
  detected_expressions: string[];
  subject: string;
  processing_info: {
    ocr_confidence: number;
    math_detected: boolean;
    image_quality: string;
  };
}

interface VisualQAProps {
  onResult?: (result: VisualQAResult) => void;
}

export default function VisualQA({ onResult }: VisualQAProps) {
  const [image, setImage] = useState<File | null>(null);
  const [imagePreview, setImagePreview] = useState<string>("");
  const [question, setQuestion] = useState("");
  const [subject, setSubject] = useState("general");
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<VisualQAResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const fileInputRef = useRef<HTMLInputElement>(null);

  const handleImageUpload = (event: React.ChangeEvent<HTMLInputElement>) => {
    const file = event.target.files?.[0];
    if (file) {
      if (file.size > 10 * 1024 * 1024) { // 10MB limit
        setError("Image size must be less than 10MB");
        return;
      }
      
      if (!file.type.startsWith('image/')) {
        setError("Please upload a valid image file");
        return;
      }

      setImage(file);
      setError(null);
      
      // Create preview
      const reader = new FileReader();
      reader.onload = (e) => {
        setImagePreview(e.target?.result as string);
      };
      reader.readAsDataURL(file);
    }
  };

  const handleRemoveImage = () => {
    setImage(null);
    setImagePreview("");
    setResult(null);
    if (fileInputRef.current) {
      fileInputRef.current.value = "";
    }
  };

  const handleSubmit = async () => {
    if (!image || !question.trim()) {
      setError("Please upload an image and enter a question");
      return;
    }

    setLoading(true);
    setError(null);

    try {
      const formData = new FormData();
      formData.append('image', image);
      formData.append('question', question);
      formData.append('subject', subject);

      const response = await fetch('/api/v1/visual-qa', {
        method: 'POST',
        body: formData,
      });

      if (!response.ok) {
        throw new Error('Failed to process image');
      }

      const data = await response.json();
      setResult(data);
      onResult?.(data);
    } catch (err: any) {
      setError(err.message || "Failed to process image");
    } finally {
      setLoading(false);
    }
  };

  const subjects = [
    { value: "general", label: "General" },
    { value: "math", label: "Mathematics" },
    { value: "physics", label: "Physics" },
    { value: "chemistry", label: "Chemistry" },
    { value: "biology", label: "Biology" },
  ];

  return (
    <div className="space-y-6">
      {/* Image Upload Section */}
      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-4">Upload Image</h3>
        
        {!image ? (
          <div
            className="border-2 border-dashed border-white/30 rounded-lg p-8 text-center hover:border-white/50 transition-colors cursor-pointer"
            onClick={() => fileInputRef.current?.click()}
          >
            <Upload className="h-12 w-12 text-white/40 mx-auto mb-4" />
            <p className="text-white/80 mb-2">Click to upload an image</p>
            <p className="text-sm text-white/60">PNG, JPG, GIF up to 10MB</p>
            <input
              ref={fileInputRef}
              type="file"
              accept="image/*"
              onChange={handleImageUpload}
              className="hidden"
            />
          </div>
        ) : (
          <div className="space-y-4">
            <div className="relative">
              <img
                src={imagePreview}
                alt="Uploaded"
                className="w-full max-h-64 object-contain rounded-lg bg-white/5"
              />
              <button
                onClick={handleRemoveImage}
                className="absolute top-2 right-2 p-1 bg-red-500/80 hover:bg-red-500 rounded-full transition-colors"
              >
                <X className="h-4 w-4 text-white" />
              </button>
            </div>
            <div className="text-sm text-white/60">
              {image.name} ({(image.size / 1024 / 1024).toFixed(2)} MB)
            </div>
          </div>
        )}
      </div>

      {/* Question Input */}
      <div className="card">
        <h3 className="text-lg font-semibold text-white mb-4">Ask a Question</h3>
        
        <div className="space-y-4">
          <div>
            <label className="block text-sm font-medium text-white mb-2">
              Subject
            </label>
            <select
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="input-field"
            >
              {subjects.map((subj) => (
                <option key={subj.value} value={subj.value}>
                  {subj.label}
                </option>
              ))}
            </select>
          </div>

          <div>
            <label className="block text-sm font-medium text-white mb-2">
              Question
            </label>
            <textarea
              value={question}
              onChange={(e) => setQuestion(e.target.value)}
              rows={3}
              placeholder="What do you want to know about this image?"
              className="input-field resize-none"
            />
          </div>

          <button
            onClick={handleSubmit}
            disabled={loading || !image || !question.trim()}
            className={cn(
              "btn-primary w-full flex items-center justify-center space-x-2",
              (loading || !image || !question.trim()) && "opacity-50 cursor-not-allowed"
            )}
          >
            {loading ? (
              <>
                <Loader2 className="h-4 w-4 animate-spin" />
                <span>Processing...</span>
              </>
            ) : (
              <>
                <Camera className="h-4 w-4" />
                <span>Analyze Image</span>
              </>
            )}
          </button>
        </div>
      </div>

      {/* Error Display */}
      {error && (
        <div className="p-4 bg-red-500/20 border border-red-500/30 rounded-lg">
          <div className="flex items-center space-x-2">
            <X className="h-4 w-4 text-red-400" />
            <span className="text-red-300 text-sm">{error}</span>
          </div>
        </div>
      )}

      {/* Results */}
      {result && (
        <div className="card space-y-4 animate-fade-in">
          <h3 className="text-lg font-semibold text-white">Analysis Results</h3>
          
          <div className="p-4 bg-white/5 rounded-lg border border-white/10">
            <div className="flex items-center space-x-2 mb-2">
              <ImageIcon className="h-4 w-4 text-green-400" />
              <span className="text-sm text-white/60">Answer</span>
            </div>
            <p className="text-white font-medium">{result.answer}</p>
            <div className="text-xs text-white/60 mt-1">
              Confidence: {(result.confidence * 100).toFixed(1)}%
            </div>
          </div>

          {result.extracted_text && (
            <div className="p-4 bg-white/5 rounded-lg border border-white/10">
              <div className="text-sm text-white/60 mb-2">Extracted Text</div>
              <p className="text-white text-sm">{result.extracted_text}</p>
            </div>
          )}

          {result.detected_expressions.length > 0 && (
            <div className="p-4 bg-white/5 rounded-lg border border-white/10">
              <div className="text-sm text-white/60 mb-2">Mathematical Expressions</div>
              <div className="flex flex-wrap gap-2">
                {result.detected_expressions.map((expr, i) => (
                  <span
                    key={i}
                    className="px-2 py-1 bg-blue-500/20 border border-blue-500/30 rounded text-sm text-blue-300"
                  >
                    {expr}
                  </span>
                ))}
              </div>
            </div>
          )}

          <div className="grid grid-cols-1 sm:grid-cols-3 gap-4 text-sm">
            <div className="p-3 bg-white/5 rounded border border-white/10">
              <div className="text-white/60">OCR Confidence</div>
              <div className="text-white font-medium">
                {(result.processing_info.ocr_confidence * 100).toFixed(1)}%
              </div>
            </div>
            <div className="p-3 bg-white/5 rounded border border-white/10">
              <div className="text-white/60">Math Detected</div>
              <div className="text-white font-medium">
                {result.processing_info.math_detected ? "Yes" : "No"}
              </div>
            </div>
            <div className="p-3 bg-white/5 rounded border border-white/10">
              <div className="text-white/60">Image Quality</div>
              <div className="text-white font-medium capitalize">
                {result.processing_info.image_quality}
              </div>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}