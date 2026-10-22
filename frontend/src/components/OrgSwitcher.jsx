
export default function OrgSwitcher({ org,val,onChange }){
    return (
            <div className="flex w-full items-center align-middle">
                <span>Organization</span>
                <select value={val} onChange={(e) => onChange(e.target.val)}>
                {org.map((o) => (
                    <option key={o.slug} >{o.name}</option>
                ))}
                </select>
            </div>
    );
}