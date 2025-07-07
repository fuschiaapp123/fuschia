import React, { useState } from 'react';

    import {
    Menubar,
    MenubarContent,
    MenubarItem,
    MenubarMenu,
    MenubarSeparator,
    MenubarShortcut,
    MenubarTrigger,
  } from "./ui/menubar"


const Menu = ({ onSave, fileName, setFileName, onLoadFlow, onAddNode }) => {
   
    const [exportDialogOpen, setExportDialogOpen] = useState(false);

    const handleSaveClick = () => {
        setExportDialogOpen(true);
      };
    const handleCancel = () => {
        setExportDialogOpen(false);
      };

    return (
        <div style={{/* existing sidebar styles */
            position: 'absolute',
            left: 800,
            top: 10,
            width: 350,
            background: 'white',
            padding: '10px',
            borderRadius: '8px',
            boxShadow: '0 2px 4px rgba(0,0,0,0.1)',
            zIndex: 1000
          }}>
        <Menubar>
            <MenubarMenu>
                <MenubarTrigger>File</MenubarTrigger>
                <MenubarContent>

                    <input
                        accept=".yaml,.yml"
                        style={{ display: 'none' }}
                        id="load-workflow"
                        type="file"
                        onChange={onLoadFlow}
                    />
                    <label htmlFor="load-workflow">
                        <MenubarItem onClick={onLoadFlow}>Load</MenubarItem>
                    </label>
                    <MenubarItem onClick={handleSaveClick}>Save</MenubarItem>
                    
                    
                <MenubarSeparator />
                <MenubarItem>Share</MenubarItem>
                <MenubarSeparator />
                <MenubarItem>Print</MenubarItem>
                </MenubarContent>
            </MenubarMenu>
            <MenubarMenu>
                <MenubarTrigger>Edit</MenubarTrigger>
                <MenubarContent>
                    <MenubarItem onClick={onAddNode}>Add Node</MenubarItem>
                    <MenubarItem>Delete</MenubarItem>
                </MenubarContent>
            </MenubarMenu>  
        </Menubar>
        {exportDialogOpen && (
                    <div className="bg-white p-6 rounded-lg shadow-lg w-96">
                        <h3 className="text-lg font-medium mb-4">Save File</h3>
                        <input
                        type="text"
                        value={fileName}
                        onChange={(e) => setFileName(e.target.value)}
                        className="w-full px-3 py-2 border border-gray-300 rounded mb-4 focus:outline-none focus:ring-2 focus:ring-blue-500"
                        placeholder="Enter filename"
                        autoFocus
                        />
                        <div className="flex justify-end space-x-2">
                            <button 
                                onClick={handleCancel}
                                className="bg-gray-200 hover:bg-gray-300 px-4 py-2 rounded"
                            >
                                Cancel
                            </button>
                            <button 
                                onClick={onSave}
                                className="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded"
                            >
                                Save
                            </button>
                        </div>
                    </div>
                    )}
        </div>
    );

}

export default Menu;