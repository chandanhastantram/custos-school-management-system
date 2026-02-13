import { useLocation } from "react-router-dom";

const PlaceholderPage = () => {
  const location = useLocation();
  const pageName = location.pathname.split("/").pop()?.replace(/-/g, " ") || "Page";

  return (
    <div className="space-y-4">
      <h1 className="text-2xl font-bold capitalize">{pageName}</h1>
      <p className="text-muted-foreground">This module is coming soon. Check back later!</p>
      <div className="rounded-xl border border-dashed border-border bg-muted/30 p-12 text-center">
        <p className="text-muted-foreground text-sm">Module under development</p>
      </div>
    </div>
  );
};

export default PlaceholderPage;
