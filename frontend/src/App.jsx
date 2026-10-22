import { useState } from "react";
import OrgSwitcher from "./components/OrgSwitcher.jsx";
import Main from "./pages/Main.jsx";
import './App.css'

export const Organization = [
  { slug: "northwind", name: "Northwind Ventures" },
  { slug: "bluebird", name: "Bluebird Capital" },
];

function App() {
  const [org, setOrg] = useState(['northwind']);

  function changeOrg(slug){
    setOrg(slug)
  }
  return (
    <>
      <div className="w-full h-8 items-center bg-white flex">
        <div className="w-3/4  flex ">
          <img></img>
          <span className="font-black">FundLY</span>
        </div>
        <div className="2/4">
          <OrgSwitcher
          org={Organization}
          val={org}
          onChange={changeOrg}
        />
        </div>
      </div>
      <Main/>
    </>
  )
}

export default App
