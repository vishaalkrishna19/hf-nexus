import React from 'react';
import {
  DndContext,
  closestCenter,
  KeyboardSensor,
  PointerSensor,
  useSensor,
  useSensors,
  DragOverlay,
  useDroppable,
} from '@dnd-kit/core';
import {
  SortableContext,
  sortableKeyboardCoordinates,
  verticalListSortingStrategy,
  useSortable,
} from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import MoreVertIcon from '@mui/icons-material/MoreVert';
import './Kanban.scss';

const CandidateCard = ({ candidate, columnId, onProceed, onReject, isDragOverlay = false }) => {
  const [showDropdown, setShowDropdown] = React.useState(false);
  
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({ 
    id: candidate.id,
    disabled: isDragOverlay
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition: isDragging ? 'none' : transition,
  };

  const handleMoreActionsClick = (e) => {
    e.stopPropagation();
    setShowDropdown(!showDropdown);
  };

  const handleActionClick = (action, e) => {
    e.stopPropagation();
    setShowDropdown(false);
    
    switch(action) {
      case 'proceed':
        onProceed(candidate.id, columnId);
        break;
      case 'reject':
        onReject(candidate.id, columnId);
        break;
      case 'view':
        // Handle view action
        break;
    }
  };

  React.useEffect(() => {
    const handleClickOutside = () => setShowDropdown(false);
    if (showDropdown) {
      document.addEventListener('click', handleClickOutside);
      return () => document.removeEventListener('click', handleClickOutside);
    }
  }, [showDropdown]);

return (
    <div
        ref={setNodeRef}
        style={style}
        {...(!isDragOverlay ? attributes : {})}
        {...(!isDragOverlay ? listeners : {})}
        className={`candidate-card ${isDragging ? 'dragging' : ''} ${isDragOverlay ? 'drag-overlay' : ''}`}
    >
        <div className="candidate-card__banner">
            <div className="banner-label">Interview</div>
            <div className="banner-date">
                <i className="fas fa-calendar"></i>
                <span>Today, 2:30 PM</span>
            </div>
        </div>

        <div className="candidate-card__content">
            <div className="candidate-card__header">
                <div className="candidate-card__header__info">
                    <h3>{candidate.name}</h3>
                    <span className="candidate-card__header__role">{candidate.role}</span>
                </div>
                
                {!isDragOverlay && (
                    <div className="candidate-card__actions">
                        <button 
                            className={`more-actions-btn ${showDropdown ? 'active' : ''}`}
                            onClick={handleMoreActionsClick}
                        >
                            <MoreVertIcon fontSize="small" />
                        </button>
                        
                        <div className={`actions-dropdown ${showDropdown ? 'show' : ''}`}>
                            <button 
                                className="dropdown-item proceed"
                                onClick={(e) => handleActionClick('proceed', e)}
                            >
                                <i className="fas fa-arrow-right"></i>
                                <span>Proceed</span>
                            </button>
                            <button 
                                className="dropdown-item view"
                                onClick={(e) => handleActionClick('view', e)}
                            >
                                <i className="fas fa-eye"></i>
                                <span>View</span>
                            </button>
                            <button 
                                className="dropdown-item reject"
                                onClick={(e) => handleActionClick('reject', e)}
                            >
                                <i className="fas fa-times"></i>
                                <span>Reject</span>
                            </button>
                        </div>
                    </div>
                )}
            </div>
        </div>
    </div>
);
};

const DroppableColumn = ({ column, onProceed, onReject }) => {
  const { setNodeRef, isOver } = useDroppable({
    id: column.id,
  });

  return (
    <div className="kanban-column">
      <div className="kanban-column__header">
        <h2>{column.title}</h2>
        <span className="candidate-count">{column.candidates.length}</span>
      </div>
      
      <div 
        ref={setNodeRef}
        className={`kanban-column__content ${isOver ? 'drag-over' : ''}`}
      >
        <SortableContext 
          items={column.candidates.map(c => c.id)} 
          strategy={verticalListSortingStrategy}
        >
          {column.candidates.map((candidate) => (
            <CandidateCard
              key={candidate.id}
              candidate={candidate}
              columnId={column.id}
              onProceed={onProceed}
              onReject={onReject}
            />
          ))}
        </SortableContext>
        {column.candidates.length === 0 && (
          <div className="kanban-column__empty">
            <p>Drop candidates here</p>
          </div>
        )}
      </div>
    </div>
  );
};

const Kanban = ({ columns, onProceed, onReject, onDragEnd }) => {
  const [activeCandidate, setActiveCandidate] = React.useState(null);
  
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8,
      },
    }),
    useSensor(KeyboardSensor, {
      coordinateGetter: sortableKeyboardCoordinates,
    })
  );

  const handleDragStart = (event) => {
    const { active } = event;
    
    // Find the candidate being dragged
    let candidate = null;
    columns.forEach(column => {
      const foundCandidate = column.candidates.find(c => c.id === active.id);
      if (foundCandidate) {
        candidate = foundCandidate;
      }
    });
    
    setActiveCandidate(candidate);
  };

  const handleDragEnd = (event) => {
    const { active, over } = event;
    
    setActiveCandidate(null);
    
    if (!over) return;

    // Find which column the active item belongs to
    let activeColumn = null;
    columns.forEach(column => {
      if (column.candidates.some(c => c.id === active.id)) {
        activeColumn = column.id;
      }
    });

    // The over.id could be either a column id or a candidate id
    let overColumn = null;
    
    // Check if over.id is a column id
    if (columns.some(col => col.id === over.id)) {
      overColumn = over.id;
    } else {
      // If not, find which column the over candidate belongs to
      columns.forEach(column => {
        if (column.candidates.some(c => c.id === over.id)) {
          overColumn = column.id;
        }
      });
    }

    if (activeColumn && overColumn && activeColumn !== overColumn) {
      onDragEnd({
        source: { droppableId: activeColumn },
        destination: { droppableId: overColumn },
        draggableId: active.id.toString()
      });
    }
  };

  return (
    <DndContext
      sensors={sensors}
      collisionDetection={closestCenter}
      onDragStart={handleDragStart}
      onDragEnd={handleDragEnd}
    >
      <div className="kanban-board">
        {columns.map(column => (
          <DroppableColumn
            key={column.id}
            column={column}
            onProceed={onProceed}
            onReject={onReject}
          />
        ))}
      </div>
      
      <DragOverlay>
        {activeCandidate ? (
          <CandidateCard
            candidate={activeCandidate}
            columnId=""
            onProceed={() => {}}
            onReject={() => {}}
            isDragOverlay={true}
          />
        ) : null}
      </DragOverlay>
    </DndContext>
  );
};

export default Kanban;
