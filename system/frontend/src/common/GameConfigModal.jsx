import { useState, useEffect } from 'react';

const CATEGORIES = [
  { id: 'cultural', label: 'A: Cultural' },
  { id: 'demographic', label: 'B: Demographic' },
  { id: 'biological', label: 'C: Biological' },
  { id: 'co-occurrence', label: 'D: Co-occurrence' },
  { id: 'realism', label: 'E: Realism' },
  { id: 'number & spatial', label: 'F: Number & Spatial' }
];

export default function GameConfigModal({ isOpen, onClose, onSave, initialConfig }) {
  const [selectedCategories, setSelectedCategories] = useState(
    initialConfig?.selectedCategories || CATEGORIES.map(cat => cat.id)
  );

  useEffect(() => {
    if (initialConfig) {
      setSelectedCategories(initialConfig.selectedCategories || CATEGORIES.map(cat => cat.id));
    }
  }, [initialConfig]);

  const handleCategoryChange = (categoryId) => {
    setSelectedCategories(prev => {
      if (prev.includes(categoryId)) {
        return prev.filter(id => id !== categoryId);
      } else {
        return [...prev, categoryId];
      }
    });
  };

  const handleSelectAll = () => {
    setSelectedCategories(CATEGORIES.map(cat => cat.id));
  };

  const handleDeselectAll = () => {
    setSelectedCategories([]);
  };

  const handleSave = () => {
    if (selectedCategories.length === 0) {
      alert('Please select at least one category');
      return;
    }
    onSave({
      selectedCategories
    });
    onClose();
  };

  if (!isOpen) return null;

  return (
    <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
      <div className="bg-white rounded-xl p-8 max-w-2xl w-full mx-4 max-h-[90vh] overflow-y-auto">
        <h2 className="text-2xl font-bold mb-6 font-gooper">Game Configuration</h2>
        
        {/* Rounds Display */}
        <div className="mb-8">
          <h3 className="text-xl font-semibold mb-4">Number of Rounds</h3>
          <div className="p-4 bg-gray-100 rounded-lg">
            <span className="text-2xl font-bold text-blue-600">{selectedCategories.length}</span>
            <span className="text-lg ml-2">rounds (automatically determined by selected categories)</span>
          </div>
        </div>

        {/* Categories Selection */}
        <div className="mb-8">
          <div className="flex justify-between items-center mb-4">
            <h3 className="text-xl font-semibold">Image Categories</h3>
            <div className="space-x-2">
              <button
                onClick={handleSelectAll}
                className="text-sm px-3 py-1 bg-gray-200 rounded hover:bg-gray-300"
              >
                Select All
              </button>
              <button
                onClick={handleDeselectAll}
                className="text-sm px-3 py-1 bg-gray-200 rounded hover:bg-gray-300"
              >
                Deselect All
              </button>
            </div>
          </div>
          <div className="grid grid-cols-1 gap-3">
            {CATEGORIES.map(category => (
              <label key={category.id} className="flex items-center p-3 border rounded-lg hover:bg-gray-50">
                <input
                  type="checkbox"
                  checked={selectedCategories.includes(category.id)}
                  onChange={() => handleCategoryChange(category.id)}
                  className="mr-3"
                />
                <div>
                  <span className="font-medium">{category.label}</span>
                </div>
              </label>
            ))}
          </div>
          <div className="text-sm text-gray-600 mt-2">
            Selected: {selectedCategories.length} / {CATEGORIES.length} categories
          </div>
        </div>

        {/* Buttons */}
        <div className="flex justify-end space-x-4">
          <button
            onClick={onClose}
            className="px-6 py-2 border border-gray-300 rounded-lg hover:bg-gray-50"
          >
            Cancel
          </button>
          <button
            onClick={handleSave}
            className="px-6 py-2 bg-black text-white rounded-lg hover:bg-gray-800"
          >
            Save Configuration
          </button>
        </div>
      </div>
    </div>
  );
}