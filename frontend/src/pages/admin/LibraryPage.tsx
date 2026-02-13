import React, { useState } from "react";
import { motion } from "framer-motion";
import { 
  Book, Search, Filter, Plus, 
  Trash2, Edit, BookOpen, Clock, 
  User, CheckCircle2, AlertCircle, 
  ArrowUpRight, BarChart3, Library
} from "lucide-react";
import { Button } from "@/components/ui/button";
import { Input } from "@/components/ui/input";
import { Badge } from "@/components/ui/badge";
import { Card, CardContent, CardHeader, CardTitle, CardDescription } from "@/components/ui/card";
import { 
  Table, TableBody, TableCell, 
  TableHead, TableHeader, TableRow 
} from "@/components/ui/table";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { 
  Dialog, DialogContent, DialogHeader, 
  DialogTitle, DialogDescription, DialogFooter 
} from "@/components/ui/dialog";
import { cn } from "@/lib/utils";
import { toast } from "sonner";

// Demo data
const DEMO_BOOKS = [
  { id: "1", title: "Objective Mathematics", author: "R.D. Sharma", category: "Textbook", isbn: "978-81-318-0853-2", total: 45, available: 12, location: "Shelf A-1" },
  { id: "2", title: "Concepts of Physics", author: "H.C. Verma", category: "Textbook", isbn: "978-81-770-9187-8", total: 30, available: 5, location: "Shelf B-4" },
  { id: "3", title: "A Brief History of Time", author: "Stephen Hawking", category: "Science", isbn: "978-05-533-8016-3", total: 10, available: 8, location: "Shelf C-2" },
  { id: "4", title: "The God of Small Things", author: "Arundhati Roy", category: "Fiction", isbn: "978-06-794-5731-2", total: 5, available: 0, location: "Shelf D-1" },
];

const DEMO_ISSUES = [
  { id: "1", student: "Aisha Singh", book: "Objective Mathematics", date: "2024-11-10", due: "2024-11-24", status: "active" },
  { id: "2", student: "Rahul Verma", book: "A Brief History of Time", date: "2024-11-05", due: "2024-11-19", status: "overdue" },
];

const LibraryPage = () => {
  const [searchTerm, setSearchTerm] = useState("");
  const [isAddBookOpen, setIsAddBookOpen] = useState(false);

  const filteredBooks = DEMO_BOOKS.filter(b => 
    b.title.toLowerCase().includes(searchTerm.toLowerCase()) ||
    b.author.toLowerCase().includes(searchTerm.toLowerCase())
  );

  return (
    <div className="space-y-6">
      <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold">Library Management</h1>
          <p className="text-muted-foreground text-sm">Manage books, issues, and digital resources</p>
        </div>
        <div className="flex items-center gap-2">
          <Button onClick={() => setIsAddBookOpen(true)}>
            <Plus className="h-4 w-4 mr-2" /> Add New Book
          </Button>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
        {[
          { label: "Total Books", value: "1,245", icon: Book, color: "text-blue-600 bg-blue-50" },
          { label: "Issued Today", value: "24", icon: ArrowUpRight, color: "text-emerald-600 bg-emerald-50" },
          { label: "Overdue", value: "12", icon: AlertCircle, color: "text-red-600 bg-red-50" },
          { label: "Total Members", value: "850", icon: User, color: "text-purple-600 bg-purple-50" },
        ].map((stat) => (
          <Card key={stat.label}>
            <CardContent className="p-4 flex items-center gap-3">
              <div className={cn("h-10 w-10 rounded-lg flex items-center justify-center", stat.color)}>
                <stat.icon className="h-5 w-5" />
              </div>
              <div>
                <p className="text-xs text-muted-foreground">{stat.label}</p>
                <p className="text-xl font-bold">{stat.value}</p>
              </div>
            </CardContent>
          </Card>
        ))}
      </div>

      <Tabs defaultValue="catalog" className="w-full">
        <TabsList className="bg-muted/50 p-1">
          <TabsTrigger value="catalog" className="data-[state=active]:bg-background">Book Catalog</TabsTrigger>
          <TabsTrigger value="issues" className="data-[state=active]:bg-background">Issue Registry</TabsTrigger>
          <TabsTrigger value="requests" className="data-[state=active]:bg-background">Requests</TabsTrigger>
        </TabsList>

        <TabsContent value="catalog" className="mt-6 space-y-4">
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search by title, author or ISBN..."
                className="pl-9"
                value={searchTerm}
                onChange={(e) => setSearchTerm(e.target.value)}
              />
            </div>
            <Button variant="outline">
              <Filter className="h-4 w-4 mr-2" /> Filters
            </Button>
          </div>

          <Card>
            <CardContent className="p-0">
              <Table>
                <TableHeader>
                  <TableRow>
                    <TableHead className="w-[300px]">Book Title</TableHead>
                    <TableHead>Author</TableHead>
                    <TableHead>Category</TableHead>
                    <TableHead className="text-center">Stock</TableHead>
                    <TableHead>Location</TableHead>
                    <TableHead className="text-right">Actions</TableHead>
                  </TableRow>
                </TableHeader>
                <TableBody>
                  {filteredBooks.map((book) => (
                    <TableRow key={book.id}>
                      <TableCell>
                        <div className="flex flex-col">
                          <span className="font-medium">{book.title}</span>
                          <span className="text-xs text-muted-foreground font-mono">{book.isbn}</span>
                        </div>
                      </TableCell>
                      <TableCell>{book.author}</TableCell>
                      <TableCell>
                        <Badge variant="secondary" className="text-[10px] uppercase">{book.category}</Badge>
                      </TableCell>
                      <TableCell className="text-center">
                        <div className="flex flex-col items-center">
                          <span className={cn(
                            "text-sm font-bold",
                            book.available === 0 ? "text-red-500" : book.available < 5 ? "text-amber-500" : "text-emerald-500"
                          )}>
                            {book.available}/{book.total}
                          </span>
                          <div className="w-12 h-1 bg-muted rounded-full mt-1 overflow-hidden">
                            <div 
                              className={cn(
                                "h-full",
                                book.available === 0 ? "bg-red-500" : book.available < 5 ? "bg-amber-500" : "bg-emerald-500"
                              )} 
                              style={{ width: `${(book.available/book.total)*100}%` }} 
                            />
                          </div>
                        </div>
                      </TableCell>
                      <TableCell className="text-xs font-medium text-muted-foreground">{book.location}</TableCell>
                      <TableCell className="text-right">
                        <div className="flex items-center justify-end gap-1">
                          <Button variant="ghost" size="icon" className="h-8 w-8">
                            <Edit className="h-4 w-4" />
                          </Button>
                          <Button variant="ghost" size="icon" className="h-8 w-8 text-red-500">
                            <Trash2 className="h-4 w-4" />
                          </Button>
                        </div>
                      </TableCell>
                    </TableRow>
                  ))}
                </TableBody>
              </Table>
            </CardContent>
          </Card>
        </TabsContent>

        <TabsContent value="issues" className="mt-6">
          <Card>
            <Table>
              <TableHeader>
                <TableRow>
                  <TableHead>Student Name</TableHead>
                  <TableHead>Book Title</TableHead>
                  <TableHead>Issue Date</TableHead>
                  <TableHead>Due Date</TableHead>
                  <TableHead>Status</TableHead>
                  <TableHead className="text-right">Actions</TableHead>
                </TableRow>
              </TableHeader>
              <TableBody>
                {DEMO_ISSUES.map((issue) => (
                  <TableRow key={issue.id}>
                    <TableCell className="font-medium">{issue.student}</TableCell>
                    <TableCell>{issue.book}</TableCell>
                    <TableCell className="text-sm">{issue.date}</TableCell>
                    <TableCell className="text-sm">{issue.due}</TableCell>
                    <TableCell>
                      <Badge className={cn(
                        "uppercase text-[10px]",
                        issue.status === "active" ? "bg-blue-100 text-blue-700 hover:bg-blue-100" : "bg-red-100 text-red-700 hover:bg-red-100"
                      )}>
                        {issue.status}
                      </Badge>
                    </TableCell>
                    <TableCell className="text-right">
                      <Button variant="outline" size="sm">Return Book</Button>
                    </TableCell>
                  </TableRow>
                ))}
              </TableBody>
            </Table>
          </Card>
        </TabsContent>
      </Tabs>

      {/* Add Book Modal */}
      <Dialog open={isAddBookOpen} onOpenChange={setIsAddBookOpen}>
        <DialogContent className="sm:max-w-[600px]">
          <DialogHeader>
            <DialogTitle>Add New Book</DialogTitle>
            <DialogDescription>Enter book details to add it to the library catalog.</DialogDescription>
          </DialogHeader>
          <div className="grid grid-cols-2 gap-4 py-4">
            <div className="space-y-2 col-span-2">
              <label className="text-sm font-medium">Book Title</label>
              <Input placeholder="e.g. Higher Engineering Mathematics" />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">Author</label>
              <Input placeholder="e.g. B.S. Grewal" />
            </div>
            <div className="space-y-2">
              <label className="text-sm font-medium">ISBN</label>
              <Input placeholder="e.g. 978-XXXX-XXXX" />
            </div>
          </div>
          <DialogFooter>
            <Button variant="outline" onClick={() => setIsAddBookOpen(false)}>Cancel</Button>
            <Button onClick={() => {
              toast.success("Book added to catalog!");
              setIsAddBookOpen(false);
            }}>Save Book</Button>
          </DialogFooter>
        </DialogContent>
      </Dialog>
    </div>
  );
};

export default LibraryPage;
