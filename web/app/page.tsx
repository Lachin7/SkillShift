import Link from "next/link";

export default function HomePage() {
  return (
    <main className="home">
      <div className="home-inner">
        <p className="home-kicker">SkillShift</p>
        <h1>Publish once. Adapt elsewhere.</h1>
        <p className="home-claim">
          A skill learned in Store A can acquire, repair, and persist an adapter
          for unseen Store B.
        </p>
        <div className="home-split">
          <span>Skill = WHAT</span>
          <span>Adapter = HOW HERE</span>
        </div>
        <div className="home-grid">
          <Link className="home-card" href="/store-a">
            <em>Teach</em>
            <strong>Store A</strong>
            <p>Products → Add Product → Media → Publish</p>
          </Link>
          <Link className="home-card" href="/store-b">
            <em>Transfer</em>
            <strong>Store B</strong>
            <p>Inventory → Create Listing → Go Live</p>
          </Link>
          <Link className="home-card" href="/dashboard">
            <em>Watch</em>
            <strong>Dashboard</strong>
            <p>Skill, App, Adapter, Status</p>
          </Link>
        </div>
      </div>
    </main>
  );
}
